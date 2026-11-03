from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import json
OUT=Path(__file__).resolve().parent
DOCX=OUT/'CoReTA_GPU资源评估与RTX4090申请报告_20261030.docx'
doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.67);sec.bottom_margin=Inches(.65);sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
sec.header_distance=Inches(.28);sec.footer_distance=Inches(.28)
styles=doc.styles
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
 st=styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
 st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'微软雅黑')
normal=styles['Normal'];normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.18;normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.widow_control=True
for name,size in [('Title',21),('Heading 1',14),('Heading 2',11.5),('Subtitle',10),('Caption',9.5)]:
 styles[name].font.size=Pt(size)
 styles[name].paragraph_format.space_before=Pt(9 if name.startswith('Heading') else 0)
 styles[name].paragraph_format.space_after=Pt(6)
 if name.startswith('Heading'):styles[name].font.bold=True;styles[name].paragraph_format.keep_with_next=True
styles['Title'].paragraph_format.space_after=Pt(8)
styles['Subtitle'].font.italic=False
# Remove title/style paragraph borders to keep a plain formal title.
for name in ['Title','Subtitle','Heading 1','Heading 2']:
 pp=styles[name].element.find(qn('w:pPr'))
 if pp is not None:
  for el in list(pp):
   if el.tag==qn('w:pBdr'):pp.remove(el)
props=doc.core_properties;props.title='CoReTA GPU资源评估与RTX4090申请报告';props.subject='显卡部署能力及多智能体专家研究算力需求';props.author='CoReTA研究项目组';props.keywords='GPU RTX4090 Qwen 微调 多智能体'
h=sec.header.paragraphs[0];h.text='CoReTA  研究算力资源评估';h.style=styles['Normal'];h.paragraph_format.space_after=Pt(0)
for r in h.runs:r.font.size=Pt(8.5)
f=sec.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=f.add_run('2026年10月30日  |  ');r.font.size=Pt(8.5)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
def p(text,bold=False,style=None,size=None):
 z=doc.add_paragraph(style=style);r=z.add_run(text);r.bold=bold
 if size:r.font.size=Pt(size)
 return z
def heading(text):return p(text,style='Heading 1')
def sub(text):return p(text,style='Heading 2')
def note(text):
 z=p(text,size=9.5);z.paragraph_format.space_after=Pt(5);return z
def table(headers,rows,widths,font=10):
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 pr=t._tbl.tblPr
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'5');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 pr.append(borders)
 layout=OxmlElement('w:tblLayout');layout.set(qn('w:type'),'fixed');pr.append(layout)
 for i,items in enumerate([headers]+rows):
  row=t.rows[0] if i==0 else t.add_row()
  rp=row._tr.get_or_add_trPr();ns=OxmlElement('w:cantSplit');rp.append(ns)
  if i==0:
   rep=OxmlElement('w:tblHeader');rp.append(rep)
  for j,(cell,text) in enumerate(zip(row.cells,items)):
   cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   cp=cell._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
   for edge,value in [('top',95),('bottom',95),('left',95),('right',95)]:
    x=OxmlElement('w:'+edge);x.set(qn('w:w'),str(value));x.set(qn('w:type'),'dxa');mar.append(x)
   cp.append(mar)
   shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'343F4D' if i==0 else ('F3F6F8' if i%2==0 else 'FFFFFF'));cp.append(shade)
   para=cell.paragraphs[0];para.paragraph_format.space_after=Pt(0);para.paragraph_format.line_spacing=1.12
   para.paragraph_format.keep_with_next=False
   para.alignment=WD_ALIGN_PARAGRAPH.CENTER if i==0 or j==0 else WD_ALIGN_PARAGRAPH.LEFT
   run=para.add_run(text);run.font.size=Pt(font);run.bold=i==0;run.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '000000')
   run.font.name='Calibri';run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'微软雅黑')
 doc.add_paragraph().paragraph_format.space_after=Pt(0)
 return t
def page():doc.add_page_break()
def hyperlink(par,label,url):
 rel=par.part.relate_to(url,RT.HYPERLINK,is_external=True);el=OxmlElement('w:hyperlink');el.set(qn('r:id'),rel)
 r=OxmlElement('w:r');pr=OxmlElement('w:rPr');co=OxmlElement('w:color');co.set(qn('w:val'),'000000');pr.append(co)
 under=OxmlElement('w:u');under.set(qn('w:val'),'single');pr.append(under)
 size=OxmlElement('w:sz');size.set(qn('w:val'),'19');pr.append(size);r.append(pr);tx=OxmlElement('w:t');tx.text=label;r.append(tx);el.append(r);par._p.append(el)
# PAGE 1
p('CoReTA显卡部署能力与算力申请报告',style='Title')
p('供导师评估  2026年10月30日',style='Subtitle')
p('建议优先申请单张RTX 4090 24GB及可预约的稳定使用时段，用于Qwen 4B与8B模型的专家适配器微调、能力校准和多轮团队实验。4090D或3090 24GB可作备选；现有双2080 Ti适合先做4B可行性验证。',bold=True)
p('项目研究具有实际任务优势的成员为何未被团队充分利用，以及怎样保留有益纠错。算力申请主要服务于可控专家构造和重复对照实验，不以部署最大模型为目标。')
heading('一 显卡与模型部署范围')
note('下表为工程估算。标准2080 Ti按每卡11GB，3090、4090和原版4090D按每卡24GB；实际版本、空闲显存和服务器状态待核。推理先按单活跃会话、8K至16K总上下文测试。[1–4]')
main_rows=[
['双1080 Ti\n11GB × 2','3B短输入可试\n4B须看缓存','4B或7至8B可试\n软件与速度需核','小模型适配器仅作探索\n不建议主训练','备用推理与接口验证'],
['双2080 Ti\n11GB × 2','3B短输入起步\n8B需双卡分片','4B与8B优先\n14B分片可试','先4B QLoRA\n8B需测长度与显存','可启动小规模验证\n不是单张22GB卡'],
['RTX 3090\n24GB','4B与8B优先\n14B FP16装不下','8B与14B优先\n32B属边界尝试','4B与8B QLoRA\n14B短序列待测','实用备选\n单卡简化部署'],
['RTX 4090\n24GB','4B与8B优先\n14B FP16装不下','8B与14B优先\n32B属边界尝试','4B与8B QLoRA\n14B待实测','优先申请\n兼顾训练与反复推理'],
['RTX 4090D\n24GB','与其他24GB卡\n同容量范围','与其他24GB卡\n同容量范围','4B与8B QLoRA\n具体速度实测','可接受备选\n显存并不高于4090']]
table(['显卡','非量化推理','4bit量化推理','专家微调','项目定位'],main_rows,[1.02,1.3,1.5,1.5,1.58],font=9.7)
note('实用范围不是绝对上限。32B的4bit模型可能在短输入、低并发下装入24GB，但不作为长讨论或微调的默认配置。以上训练建议均指LoRA或QLoRA，不指全参数训练。')
# PAGE 2
page();heading('二 显存占用与部署边界')
p('完整模型加载用于推理，与全参数微调是两件事。3B模型的FP16纯权重约6GB，11GB显卡可作为短输入起点；训练还需梯度、优化器和反向传播中间结果，不能据权重大小判断能否训练。[8]')
table(['显存组成','用途','主要增长因素'],[
['模型权重','存放模型参数；量化可减少存储','参数量、精度及非量化模块'],
['KV缓存','复用已读文本的计算结果','上下文长度、生成长度、并发数'],
['计算与框架','中间张量、注意力、CUDA工作区','长输入、批量及注意力实现'],
['微调附加项','梯度、优化器状态、训练激活及LoRA','可训练参数、样本长度和训练方式']],[1.15,2.8,2.95],font=10)
sub('纯权重估算')
table(['模型规模','FP16或BF16权重','理想4bit权重'],[
['3B 泛指','6.0 GB','1.5 GB'],['Qwen3 4B','8.0 GB','2.0 GB'],['Qwen3 8B','16.4 GB','4.1 GB'],['Qwen3 14B','29.6 GB','7.4 GB'],['Qwen3 32B','65.6 GB','16.4 GB']],[2.3,2.3,2.3],font=10)
note('按官方约4.0、8.2、14.8、32.8B参数推算。GB采用十进制。4bit列未计量化元数据和非量化层；两列均未计缓存与工作区，不是运行显存。[5–7]')
p('以Qwen3 4B与8B为例，按一个活跃会话、FP16 KV缓存估算，8K、16K、32K长度的缓存约为1.125、2.25、4.5 GiB。多轮讨论历史和生成内容会持续增长；实际还需计入预填充峰值。')
p('双11GB显卡不会自动合并成单张22GB。分片部署需单独配置并承担通信开销；普通数据并行复制模型，不能解决每卡装不下。2080 Ti的Turing架构也需单独核验FP16、量化及注意力内核，不能照搬4090的BF16配置。[8–9]')
# PAGE 3
page();heading('三 项目需要的模型与服务器条件')
p('优先候选是同一Qwen底座加一个任务LoRA：普通成员使用底座，专家成员使用底座与适配器，再通过独立题目确认能力优势。四名逻辑agent可顺序调用同一份底座，各自保留独立上下文，不需同时常驻四份完整模型。')
table(['项目环节','起步方案','申请4090后的目标'],[
['基础推理','4B量化完整题目测试','4B与8B对比，视显存选择FP16或量化'],
['专家构造','先验证4B QLoRA小步训练','优先测试8B QLoRA，保留4B比较'],
['团队交流','独答与逐发言历史完整保存','测试多轮讨论和完整终答，不为显存删证据'],
['上下文预算','先测8K至16K总上下文','16K实测通过后再探索32K；不保证必能容纳'],
['训练序列','按完整样本长度分布确定','2K或4K可用于预检，正式训练不默认截断'],
['结果验证','独立校准与普通团队基线','增加必要重复、对照和失败分析']],[1.22,2.68,3.0],font=10)
sub('配套服务器建议')
table(['项目','建议配置','说明'],[
['GPU','优先单张RTX 4090 24GB','4090D或3090 24GB可备选'],
['主机内存','64GB起步，128GB更宽裕','供模型加载、数据处理及必要卸载；建议值'],
['存储','建议预留200GB SSD工作空间','按模型缓存、检查点与日志实际占用调整'],
['系统环境','Linux及匹配的驱动和PyTorch环境','固定模型与依赖版本，旧卡兼容另测'],
['使用方式','SSH或作业队列及稳定预约时段','先核实际权限与空闲显存，再安排运行']],[1.22,2.68,3.0],font=10)
p('4B与8B已有协作研究先例。ICR采用Qwen3 4B及8B；When Debate Helps采用4B与7B的四成员多轮轨迹。因此，小参数模型可以承担正式实证研究，但本项目是否产生足够的专家优势与正负交互事件，仍由校准和开发实验决定。[10–11]')
# PAGE 4
page();heading('四 优先申请RTX 4090的依据')
sub('研究用途与预期收益')
p('第一，支持更合适的8B候选。相对每卡11GB的双2080 Ti，单卡24GB更便于容纳底座、专家适配器、训练激活和较长输入，减少为适配显存而进行复杂跨卡切分的需要。8B能否完成具体长度的训练，仍需小步实测。')
p('第二，服务于多轮与重复实验。每题涉及成员独答、多个讨论发言、最终作答及无消息等对照；还需专家训练与独立校准。较强算力和稳定预约时段有利于缩短迭代周期，完成必要重复和错误分析。')
p('第三，减少旧架构适配负担。4090属于Ada架构，支持当前主线FlashAttention 2所列平台及BF16计算；相比2080 Ti，可减少旧架构内核适配。具体软件组合及速度收益仍以本机验证为准。[3,9]')
p('相对3090，4090的申请重点是计算性能与实验周转，而不是显存容量。两者标准显存均为24GB，不能据4090型号宣称能部署明显更大的模型，也不承诺未经测试的速度倍数。若3090可提供更稳定的使用时段，仍是有效方案。',bold=True)
sub('建议的申请方式')
p('申请单张RTX 4090 24GB的服务器使用资源，先提供一周可预约验证窗口，用于环境配置、真实任务推理、峰值显存与吞吐测量、小规模专家适配器训练及能力校准。该窗口为排期建议，不代表持续满负载或承诺一周完成全部研究。')
p('首阶段输出真实显存、吞吐、训练步耗时和校准结果，再据此核算后续GPU小时及预约周期。若4090暂不可得，依次评估可稳定使用的4090D或3090；已有双2080 Ti用于并行推进4B验证。')
sub('可直接用于申请说明的文字')
p('本项目拟研究多智能体团队对任务专家能力的利用与损失，需要在同一Qwen底座上构造任务专家适配器，并开展独立能力校准、多轮交流和重复对照实验。现有双2080 Ti可用于4B模型起步，但每卡11GB对8B微调及长输入的余量较小。拟优先申请单张RTX 4090 24GB及配套服务器使用时段，以降低部署复杂度、支持8B候选和必要的实验迭代。先进行一周可预约验证，提交实测用量后再申请后续配额；4090D或3090 24GB可作为备选。')
# PAGE 5
page();heading('五 验收安排与依据来源')
sub('首阶段完成什么')
table(['步骤','交付与判断'],[
['1 核实资源','记录实际显卡和显存、系统、驱动、主存、存储与使用权限。'],
['2 技术验证','以完整真实题目测推理、上下文增长、解析与显存峰值；记录截断和失败。'],
['3 小规模微调','确认LoRA训练、保存、重新加载可用；按实测步耗时估总量。'],
['4 科学校准','使用独立题目检查专家优势，再做普通团队、独思和初答投票比较。']],[1.5,5.4],font=10)
p('GPU部署成功不等于专家训练成功；专家形成优势也不等于团队必然受损。每个小阶段核对目标、证据与资源，再决定继续、修改或停止对应设置。当前仅完成资源与文献分析，未实测本报告中的机器，未启动模型部署或训练。')
sub('参考资料')
refs=[
('[1] NVIDIA RTX 2080 Ti官方规格','https://www.nvidia.com/content/nvidiaGDC/zz/en_ZZ/geforce/graphics-cards/rtx-2080-ti.html'),
('[2] NVIDIA RTX 3090官方规格','https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3090-3090ti/'),
('[3] NVIDIA RTX 4090官方规格','https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/'),
('[4] NVIDIA RTX 4090D官方规格','https://www.nvidia.cn/geforce/graphics-cards/40-series/rtx-4090-d/'),
('[5] Qwen3 4B官方模型卡与配置','https://huggingface.co/Qwen/Qwen3-4B'),
('[6] Qwen3 8B官方模型卡与配置','https://huggingface.co/Qwen/Qwen3-8B'),
('[7a] Qwen3 14B官方模型卡','https://huggingface.co/Qwen/Qwen3-14B'),
('[7b] Qwen3 32B官方模型卡','https://huggingface.co/Qwen/Qwen3-32B'),
('[8] Hugging Face量化与QLoRA文档','https://huggingface.co/docs/transformers/quantization/bitsandbytes'),
('[9] FlashAttention官方硬件要求','https://github.com/Dao-AILab/flash-attention#nvidia-cuda-support'),
('[10] Li等 Beyond Final Accuracy 预印本 2026','https://arxiv.org/html/2610.01042v1'),
('[11] Zhao等 When Debate Helps 预印本 2026','https://arxiv.org/html/2610.04686v1')]
for label,url in refs:
 z=doc.add_paragraph();z.paragraph_format.space_after=Pt(3);z.paragraph_format.line_spacing=1.05;hyperlink(z,label,url)
note('规格与文献核验日期为2026年10月30日。显存范围为基于参数、缓存及常见部署方式的估算；没有声称完成实机基准。3B为泛指参数规模，Qwen3实例使用4B、8B等官方型号。')
doc.save(DOCX)
(OUT/'BUILD_MANIFEST.json').write_text(json.dumps({'date':'2026-10-30','file':DOCX.name,'intended_pages':5,'purpose':'GPU resource report for advisor review and RTX4090 allocation request','tables':len(doc.tables),'reference_links':len(refs),'model_runs':0,'training_runs':0,'hardware_estimates_not_benchmarks':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(DOCX)
