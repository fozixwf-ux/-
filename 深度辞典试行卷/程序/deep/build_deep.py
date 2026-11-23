"""Verify every quotation in deep/entries.yml against its source and write deep/out/deep.json + verification log."""
import sys, os, json, csv, re, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import tib, build

TK_VOL_LETTER = {3: 'ga', 7: 'ja'}
WORK_LABEL = {
    'SR': '宗喀巴《密宗道次第廣論》藏文',
    'RL': '宗喀巴《五次第明燈》藏文',
}

def fmt_tk(work, cite):
    # cite like 3-2-383a6 or 3-2-383a6–383b1
    m = re.match(r'(\d+)-(\d+)-(\d+[ab])(\d+)(?:–(?:\d+-\d+-)?(\d+[ab])?(\d+))?$', cite)
    vol, _, f1, l1, f2, l2 = m.groups()
    loc = f'葉{f1}{l1}' if not l2 else (f'葉{f1}{l1}–{l2}' if (f2 or f1) == f1 else f'葉{f1}{l1}–{f2}{l2}')
    return f'{WORK_LABEL[work]}，全集第{vol}函（{TK_VOL_LETTER.get(int(vol), "")}），{loc}'

def fmt_derge(toh, cite):
    t = tib.get(f'D{toh}')
    m = re.match(r'(\d+x?[ab])\.(\d+)(?:–(?:(\d+x?[ab])\.)?(\d+))?$', cite)
    f1, l1, f2, l2 = m.groups()
    loc = f'葉{f1}.{l1}' + (f'–{f2 + "." if f2 and f2 != f1 else ""}{l2}' if l2 else '')
    kind = '丹珠爾' if 'tengyur' in tib._derge_file(toh) else '甘珠爾'
    return f'德格版{kind} Toh {toh}（{t.vol}函），{loc}'

def main():
    E = yaml.safe_load(open(os.path.join(HERE, 'entries.yml'), encoding='utf8'))
    log = []; errors = []
    SR, RL = tib.get('SR'), tib.get('RL')
    for e in E:
        # concordance
        e['concord'] = []
        for term in e.get('search', []):
            e['concord'].append({'term': term, 'SR': len(SR.find_all(term)[1]), 'RL': len(RL.find_all(term)[1])})
        for L in e.get('layers', []):
            w = L['work']
            if L.get('bo'):
                cite, raw = tib.extract(w, L['bo'])
                if not cite:
                    errors.append(f'{e["id"]}: Tibetan not found in {w}: {L["bo"][:30]}'); continue
                L['bo_raw'] = raw.strip('་།༌ ')
                L['bo_cite'] = fmt_tk(w, cite) if w in ('SR', 'RL') else fmt_derge(w[1:], cite)
                log.append([e['id'], L['layer'], '藏文', w, L['bo_cite'], L['bo'][:60], '已逐字比對'])
            if L.get('zh_q'):
                src = L.get('zh_src', w)
                loc = build.cb_locate(src, L['zh_q'])
                if not loc:
                    errors.append(f'{e["id"]}: Chinese not found in {src}: {L["zh_q"][:20]}'); continue
                L['zh_cite'] = loc
                log.append([e['id'], L['layer'], '漢文', src, loc, L['zh_q'][:60], '已逐字比對'])
            if L.get('sa'):
                if not build.sk_check(w, L['sa']):
                    errors.append(f'{e["id"]}: Sanskrit not found in {w}: {L["sa"][:30]}'); continue
                name, ed = build.SK[w][1], build.SK[w][2]
                L['sa_cite'] = f'{name} {L.get("ref", "")}（{ed}）'
                log.append([e['id'], L['layer'], '梵文', w, L['sa_cite'], L['sa'][:60], '已逐字比對'])
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    json.dump(E, open(os.path.join(HERE, 'out', 'deep.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'out', 'verify_log.csv'), 'w', encoding='utf8', newline='') as f:
        w = csv.writer(f); w.writerow(['條目', '層', '語種', '文獻鍵', '出處', '錨定文字（前60字）', '核驗']); w.writerows(log)
    n = {k: sum(1 for r in log if r[2] == k) for k in ('藏文', '漢文', '梵文')}
    print(f'entries={len(E)} quotes: 藏文 {n["藏文"]} 漢文 {n["漢文"]} 梵文 {n["梵文"]}')
    if errors:
        print('ERRORS:'); print('\n'.join(errors)); sys.exit(1)

if __name__ == '__main__':
    main()
