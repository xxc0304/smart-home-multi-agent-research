"""Bounded independent batch of 1/2/4 requests, single inference process."""
from contextlib import nullcontext
import hashlib,time
from b1_runtime import LocalBackend
from b1_stop_status import termination_status

class MultiBackend(LocalBackend):
    def respond_many(self,requests,remaining):
        import torch
        from transformers import set_seed
        from peft.tuners.lora.layer import LoraLayer
        n=len(requests)
        if n not in (1,2,4):raise ValueError('batch_size_1_2_4_only')
        routes=[r['actor']==self.config['expert_actor'] for r in requests]
        if len(set(routes))!=1:raise ValueError('same_adapter_route_required')
        if len({r['max_new_tokens'] for r in requests})!=1:raise ValueError('same_cap_required')
        if remaining<=0:raise ValueError('positive_remaining_required')
        if n==1:
            original=self.model.generate;observed={}
            def capture(*args,**kwargs):
                layers=[m for m in self.model.modules() if isinstance(m,LoraLayer)]
                disabled=sum(bool(m.disable_adapters) for m in layers)
                assert layers and disabled==(0 if routes[0] else len(layers))
                observed.update(lora_layers=len(layers),disabled_layers=disabled)
                y=original(*args,**kwargs);observed['output_ids']=y[0,kwargs['input_ids'].shape[-1]:].tolist();return y
            try:self.model.generate=capture;response=self.respond(requests[0],remaining)
            finally:self.model.generate=original
            response['usage'].update(observed,batch_size=1,padded_input_tokens=response['usage']['input_tokens'])
            return [response]
        tok,model=self.tokenizer,self.model;cap=requests[0]['max_new_tokens'];ids=[]
        for r in requests:
            row=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**self.config['template_kwargs'])
            if len(row)+cap>self.config['max_length']:raise ValueError('overlength_no_truncation')
            ids.append(row)
        length=max(map(len,ids));x=torch.full((n,length),tok.pad_token_id,device=self.config['device'],dtype=torch.long);mask=torch.zeros_like(x)
        for i,row in enumerate(ids):x[i,-len(row):]=torch.tensor(row,device=x.device);mask[i,-len(row):]=1
        assert all(int(mask[i].sum())==len(row) for i,row in enumerate(ids))
        set_seed(requests[0]['seed']);rngs=[torch.Generator(device=x.device).manual_seed(r['seed']) for r in requests]
        assert len({id(g) for g in rngs})==n
        state=lambda g:hashlib.sha256(g.get_state().cpu().numpy().tobytes()).hexdigest()
        before=[state(g) for g in rngs];draws=[[] for _ in requests];original=torch.multinomial
        def independent(probs,num_samples,*args,**kwargs):
            if probs.ndim!=2 or probs.shape[0]!=n or num_samples!=1:raise ValueError('unexpected_sampling_shape')
            values=[]
            for i,g in enumerate(rngs):
                v=original(probs[i:i+1],num_samples,*args,generator=g,**kwargs);draws[i].extend(v.detach().flatten().tolist());values.append(v)
            return torch.cat(values,dim=0)
        torch.cuda.synchronize();started=time.monotonic();layers=[m for m in model.modules() if isinstance(m,LoraLayer)]
        try:
            with (nullcontext() if routes[0] else model.disable_adapter()),torch.inference_mode():
                disabled=sum(bool(m.disable_adapters) for m in layers);assert layers and disabled==(0 if routes[0] else len(layers))
                torch.multinomial=independent
                y=model.generate(input_ids=x,attention_mask=mask,generation_config=self.generation_config,max_new_tokens=cap,max_time=remaining)
        finally:torch.multinomial=original
        torch.cuda.synchronize();elapsed=time.monotonic()-started
        eos=self.generation_config.eos_token_id;eos=eos if isinstance(eos,list) else [eos if eos is not None else tok.eos_token_id]
        result=[]
        for i,r in enumerate(requests):
            tail=y[i,length:].tolist();ends=[j for j,t in enumerate(tail) if t in eos]
            if ends:tail=tail[:ends[0]+1]
            assert draws[i][:len(tail)]==tail,'sampled_tokens_do_not_match_output'
            status,reason=termination_status(tail,eos,cap,elapsed,remaining)
            result.append(dict(raw_output=tok.decode(tail,skip_special_tokens=True),status=status,usage=dict(input_tokens=len(ids[i]),padded_input_tokens=length,output_tokens=len(tail),elapsed_seconds=elapsed/n,request_latency_seconds=elapsed,cost_allocation='equal_share_of_batch_generate',batch_size=n,batch_elapsed_seconds=elapsed,adapter_enabled=routes[i],lora_layers=len(layers),disabled_layers=disabled,finish_reason=reason,output_cap=cap,ended_with_eos=reason=='EOS',rng_seed=r['seed'],rng_before=before[i],rng_after=state(rngs[i]),output_ids=tail,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())))
        return result
