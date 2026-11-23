"""Build the external review kit (blind review forms, debate questions, sampling plan, agreement calculator)."""
import json, os, csv, opencc
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
HERE = os.path.dirname(os.path.abspath(__file__))
t2s = opencc.OpenCC('t2s'); S = lambda x: t2s.convert(x or '')
E = json.load(open(os.path.join(HERE, 'out', 'deep.json'), encoding='utf8'))
for k, e in enumerate(E, 1): e['no'] = f'{k:02d}'

HEAD = Font(bold=True, color='FFFFFF'); HFILL = PatternFill('solid', fgColor='7A1F1F')
WRAP = Alignment(wrap_text=True, vertical='top'); THIN = Side(style='thin', color='CDBFA8')

def sheet(wb, title, note, headers, widths, rows):
    ws = wb.create_sheet(title)
    ws.append([note]); ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    ws['A1'].alignment = WRAP; ws['A1'].font = Font(italic=True, color='6B645A'); ws.row_dimensions[1].height = 48
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=2, column=c); cell.font = HEAD; cell.fill = HFILL; cell.alignment = WRAP
    for r in rows: ws.append(r)
    for row in ws.iter_rows(min_row=3):
        for cell in row: cell.alignment = WRAP; cell.border = Border(bottom=THIN)
    for k, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(k)].width = w
    ws.freeze_panes = 'A3'
    return ws

# ---- claims to review ----
claims = []
for e in E:
    claims.append((e['no'], S(e['zh']), '性相', S(e['xing']['text']), S(e['xing'].get('basis', ''))))
    for d in e.get('dbye', []):
        claims.append((e['no'], S(e['zh']), '分类', S(f'{d["name"]}：{d.get("note","")}'), S(d.get('basis', ''))))
    for m in e.get('mtshams', []):
        claims.append((e['no'], S(e['zh']), '界限', S(m['text']), S(m.get('basis', ''))))
    for d in e.get('disputes', []):
        claims.append((e['no'], S(e['zh']), '诤论', S(d['issue'] + '——自宗：' + d.get('self', '')), ''))
    for L in e.get('layers', []):
        if L.get('zh_tr') and L.get('bo_raw'):
            claims.append((e['no'], S(e['zh']), '编者译', f'{L["bo_raw"]}\n→ {S(L["zh_tr"])}', S(L.get('bo_cite', ''))))
    tr = e.get('trans'); tr = [tr] if isinstance(tr, str) else (tr or [])
    for t in tr: claims.append((e['no'], S(e['zh']), '译名', S(t), ''))

wb = Workbook(); wb.remove(wb.active)
note_form = ('盲审表：两位审稿人各用一张，互不相见。逐条判定“同意／部分同意／不同意”，并写理由与建议修改。'
             '“编者译”一类请对照藏文原文判断译文是否准确。判定栏已设下拉选项。')
for who in ('甲', '乙'):
    ws = sheet(wb, f'审稿表（{who}）', note_form,
               ['序', '条目', '名相', '审核项', '待审陈述', '依据', '判定', '理由', '建议修改'],
               [5, 6, 16, 8, 70, 30, 10, 30, 30],
               [[k + 1, *c, '', '', ''] for k, c in enumerate(claims)])
    dv = DataValidation(type='list', formula1='"同意,部分同意,不同意"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f'G3:G{len(claims) + 2}')

# ---- debate questions ----
DQ = [
 ('01', '圆满次第', '凡观蕴等为天之修，应皆是圆满次第，以是身远离故。', '因不遍：宗喀巴说生起次第中亦有观蘊等为天之身远离；须其乐由风入中脉融而生、以之证空，方是圆满次第之身远离。'),
 ('03', '身远离', '身远离与生起次第应无差别，以所断同为庸常慢故。', '因虽成而不遍：所断虽同，能断之智大异（宗喀巴《广论》）。'),
 ('06', '四空', '四空之“空”应即空性，以名为“空”故。', '不遍：四空之“空”指空去粗分分别及其所乘之风；四空是四种心（有境），非所证之空性（境）。'),
 ('07', '基位五次第', '凡夫死时应已成就光明次第，以死光明即名基位法身故。', '不遍：宗喀巴是以道位五次第配凡夫生死之过程（《五次第明灯》叶63a–b）；死光明是所配之基位，非道位修证之光明，不可谓凡夫已成光明次第。'),
 ('08', '幻身', '生起次第究竟时所现之天身应是幻身，以是心所现、清净无碍如虹之身故。', '不遍：宗喀巴明说此虽能于芥子量中明了坚固现起全坛，然非幻身。'),
 ('08', '幻身', '幻身之近取因应是心，以幻身唯由风心所成故。', '须分身、意：身之近取因为风，前心为俱有缘；意之近取因为前心，风为俱有缘（《五次第明灯》叶214a）。'),
 ('08', '幻身', '幻身成就时应已离旧身之处所，以“与旧身分离”故。', '不遍：分离不必捨旧身之处所；《明炬论》说清净幻身住于诸蕴之笼（叶215b）。'),
 ('09', '不净幻身・清净幻身', '“不净幻身”一名应出宗喀巴，以格鲁派通用故。', "通检：宗喀巴二论皆未见此名；“清净幻身”（dag pa'i sgyu ma'i sku）则见于《五次第明灯》。"),
 ('10', '光明', '境光明、有境光明之分应遍于基、道、果，以宗喀巴所立故。', '宗喀巴原文就无学双运位之法身而立；泛用于基、道是其后之用法。'),
 ('10', '光明', '果位色身应是异于心之物质，以是色身故。', '不遍：宗喀巴说报身唯由风心所成，与法身体一而反体异；以为物质者非善说。'),
 ('11', '喻光明・义光明', '喻光明应唯于心远离究竟时生，以是心远离之究竟故。', '不遍：宗喀巴说喻光明从身远离至幻身之间生起不相违（叶99b）。'),
 ('12', '整持・随灭', '修整持、随灭即入光明，以二静虑为入光明之方便故。', '须分时位：于风点瑜伽获得能力前修之，与生起次第所修无异。'),
 ('13', '双运', '有学双运位应已离异熟身，以其身唯由风心所成故。', '不遍：宗喀巴说其时“犹应暂现任持异熟身相”。'),
 ('14', '断证二双运', '断之双运应是宗喀巴所立，以格鲁派地道教本说之故。', '通检：宗喀巴二论皆无此名，属后期教本。'),
 ('15', '扼身要', '诸派扼身要之胜处应同，以同为令风入中脉之方便故。', '不遍：圣派以心间脉轮中央为胜处（《五次第明灯》叶66a）；那洛六法以脐间拙火为主。'),
]
sheet(wb, '辩经质询题', '供辩经检验：对方立宗与所举之因，答方依条目所据原文作答。“预期答”为依本卷所引宗喀巴原文之答，审定时可据此检验条目能否经得起质询。',
      ['条目', '名相', '立宗（问难）', '预期答（依原文）', '辩经者实际答辩记录', '结论'], [6, 14, 50, 60, 40, 14],
      [[*q, '', ''] for q in DQ])

sheet(wb, '抽样与审定方案', '本卷审定之程序与通过标准。', ['项目', '内容'], [18, 110], [
 ['审稿人', '甲：格鲁派具格格西（上、下密院或三大寺之拉然巴、俄然巴）；乙：同等资格之另一位格西，或专研密集文献之学者。二人互不相见对方意见。'],
 ['审阅范围', f'试行卷全部 {len(E)} 条、{len(claims)} 项待审陈述，全数审阅（试行卷条目少，不抽样）。扩展至全书时，每章随机抽取不少于 20% 之条目，且每部至少五条。'],
 ['判定', '每项判“同意／部分同意／不同意”，并写理由。'],
 ['一致率', '以“一致率计算”表自动计算二人之百分比一致率与 Cohen κ 系数。'],
 ['通过标准', 'κ ≥ 0.60，且“不同意”者逐项有书面处理；凡二人皆判“不同意”者，必须修改或删除。'],
 ['分歧处理', '二人判定不一者，交第三位审稿人或二人会商，处理结果记入“审稿意见处理”，并于条目中标示。'],
 ['辩经检验', '“辩经质询题”交辩经者实际质询；答辩不能成立者，条目须修订。'],
 ['学界审读', '另请专研密集、胜乐或时轮文献之学者匿名审读全卷，意见单独记录。'],
 ['公开复现', '条目数据、核对程序与核验日志随卷公开；任何人可依原典电子本重跑核对。'],
])

# agreement calculator
ws = wb.create_sheet('一致率计算')
n = len(claims); rng = lambda who: f"'审稿表（{who}）'!G3:G{n + 2}"
rows = [
 ('已判项数（甲）', f'=COUNTA({rng("甲")})'), ('已判项数（乙）', f'=COUNTA({rng("乙")})'),
 ('二人皆已判之项数', f'=SUMPRODUCT(({rng("甲")}<>"")*({rng("乙")}<>""))'),
 ('一致项数', f'=SUMPRODUCT(({rng("甲")}={rng("乙")})*({rng("甲")}<>""))'),
 ('百分比一致率 Po', '=IF(B5=0,"",B6/B5)'),
]
cats = ['同意', '部分同意', '不同意']
for c in cats:
    rows.append((f'甲判“{c}”比例', f'=IF(B5=0,"",COUNTIF({rng("甲")},"{c}")/B5)'))
    rows.append((f'乙判“{c}”比例', f'=IF(B5=0,"",COUNTIF({rng("乙")},"{c}")/B5)'))
rows.append(('期望一致率 Pe', '=IF(B5=0,"",B8*B9+B10*B11+B12*B13)'))
rows.append(('Cohen κ', '=IF(OR(B5=0,B14=1),"",(B7-B14)/(1-B14))'))
rows.append(('是否达标（κ≥0.60）', '=IF(B15="","",IF(B15>=0.6,"达标","未达标"))'))
ws.append(['一致率与 κ 系数（自动计算，勿改公式）', '']); ws['A1'].font = Font(bold=True)
ws.append(['指标', '数值'])
for r in rows: ws.append(list(r))
ws.column_dimensions['A'].width = 26; ws.column_dimensions['B'].width = 18

# logs
log = list(csv.reader(open(os.path.join(HERE, 'out', 'verify_log.csv'), encoding='utf8')))
sheet(wb, '引文核验日志', '本卷全部引文之核验记录：藏文以宗喀巴全集与德格版电子本、汉文以 CBETA、梵文以校本电子本逐字比对，并由程序回取原文与叶行。',
      [S(x) for x in log[0]], [12, 8, 6, 8, 50, 50, 10], [[S(x) for x in r] for r in log[1:]])
conc = [[e['no'], S(e['zh']), c['term'], c['SR'], c['RL']] for e in E for c in e.get('concord', [])]
sheet(wb, '逐词通检', '各名相藏文词形于宗喀巴《密宗道次第广论》与《五次第明灯》藏文全文中之出现次数。',
      ['条目', '名相', '藏文词形', '《广论》', '《五次第明灯》'], [6, 22, 30, 10, 14], conc)
out = os.path.join(HERE, 'out', '审定材料.xlsx'); wb.save(out)
print('saved', out, 'claims', len(claims), 'debate', len(DQ))
