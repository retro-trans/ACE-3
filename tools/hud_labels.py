"""HUD labels (objectives, warnings, nav hints) stored beside in-mission dialogue in every live 20020X0 scene.

The labels are templates: a category word, a fullwidth colon, then a short body from a small phrase set. Each body
is translated once here, following the released 0.1.21 wording (Objective:, Warning:, Info:, Nav:, Mission Failed:,
"Warning: Nadesico B at 25％ damage", "Warning: Allied forces wiped out", "Warning: 5 minutes remaining").
    python tools/hud_labels.py            dry run: print every label of every live scene, flag unknown bodies
    python tools/hud_labels.py --write    write work/translation/en/hud_labels.json (English only)
Builders read labels() -> {scene_id: {text_id: english}}.
"""
import argparse
import json
import re
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table

OUT = ROOT/'work/translation/en/hud_labels.json'
JP = re.compile('[぀-ヿ一-鿿]')
CATEGORY = {'目標':'Objective', '目的':'Objective', '警告':'Warning', 'インフォ':'Info', 'ナビ':'Nav', 'ミッション失敗':'Mission Failed', 'ミッション成功':'Mission Complete'}
FW = str.maketrans('０１２３４５６７８９', '0123456789')
NAMES = {'ナデシコＢ':'Nadesico B', 'ナデシコＣ':'Nadesico C', '月光号':'Gekko', 'タワー':'Tower', '友軍部隊':'Allied forces', '列車':'Train',
         '援護ユニット':'Support unit', 'クラップ級軽巡洋艦':'Clop-class cruiser', 'バルチャー艦':'Vulture ship', '新型機':'New unit', '修復部隊':'Repair team',
         '防護部隊':'Escort team', '迎撃部隊':'Interceptors', '艦隊損害率':'Fleet losses', '自走兵器のチャージ率':'Mobile weapon charge'}
STATE = {'ダメージ':'at %s damage', '壊滅':'crippled', '全滅':'wiped out', '撃沈':'sunk'}
# Bodies that are not name+state templates. Units/targets keep the locked spellings.
BODY = {
 '敵戦艦の全撃破':'Destroy all enemy warships', 'ファルゲン・マッフの撃破':'Destroy the Falguen MAFFU', '敵の全撃破':'Destroy all enemies',
 '×ボタン　２回押し：　クイックターン':'× button, press twice: Quick turn', '敵の増援が出現':'Enemy reinforcements', '残り時間　５分':'5 minutes remaining',
 '残り時間　４分':'4 minutes remaining', '残り時間　２分':'2 minutes remaining', '残り時間　１分':'1 minute remaining',
 '残り時間　７分３０秒':'7:30 remaining', '残り時間　３分３０秒':'3:30 remaining', 'タイムオーバー':'Time Over',
 '右アナログスティック：　ピッチの調整':'Right stick: Pitch', 'この世界に残る':'Stay in this world', 'もう一つの世界に移動':'Go to the other world',
 '元の世界に戻る':'Return to our world', 'オウカオーの撃破':'Destroy the Oukaou', 'ターゲットの全撃破':'Destroy all targets',
 '敵の自走砲に注意':'Watch for enemy mobile guns', '砲台が攻撃準備中':'Gun battery preparing to fire', '砲台によるダメージが拡大':'Battery damage mounting',
 '敵が進軍を開始':'Enemy advancing', '敵の自走砲を制圧':'Enemy mobile guns suppressed', '敵が後退を開始':'Enemy falling back',
 'ヤクト・ドーガの撃破':'Destroy the Jagd Doga', '敵が撤退':'Enemy retreating', '砲撃が激化':'Bombardment intensifying', '砲撃を回避しろ':'Evade the bombardment',
 '指定した方向にダッシュしろ':'Dash in the marked direction', '砲撃に注意':'Watch for bombardment',
 '月光号の目標地点到達':'Gekko reaches its goal', 'ブラッディアークの撃破':'Destroy the Blood Ark', 'ブラッドアークの撃破':'Destroy the Blood Ark',
 '母艦の撃沈':'Mothership sunk', '月光号が作戦領域に到着':'Gekko has entered the area', '敵戦艦からの増援に注意':'Watch enemy ship launches',
 '月光号が進路を変更':'Gekko changing course', '月光号が目標地点に到達':'Gekko has reached its goal', '敵戦艦から敵が出現':'Enemies launching from ships',
 'ｔｙｐｅｔｈｅＥＮＤの撃破':'Destroy the typetheEND', '援護ユニットの撃墜に注意':'Do not lose the support unit', '月光号のＡＰが回復':"Gekko's AP restored",
 '援護ユニットが北側より接近中':'Support unit coming from the north', '援護ユニットが出現':'Support unit has arrived', '拠点の制圧':'Base captured',
 '友軍が進軍を開始':'Allied forces advancing', '輸送艦が領域を離脱':'Transports leave the area', 'ターゲットの撃破':'Destroy the target',
 '輸送艦の全撃破':'Destroy all transports', '友軍の壊滅に注意':'Watch for allied losses', '輸送艦の離脱':'Transport escaped', '全拠点の制圧':'Capture all bases',
 '拠点が陥落':'Base lost', 'リーダーユニットを優先して撃破しろ':'Destroy leader units first', '友軍部隊が４つ壊滅':'4 allied forces crippled',
 'ドミネーターが出現':'Dominator sighted', '友軍部隊の壊滅に注意':'Watch for allied losses', 'ドミネーターを探せ':'Find the Dominator',
 'ドミネーターが一時撤退':'Dominator has pulled back', 'ファルゲン改の撃破':'Destroy the Falguen Custom', 'ファルゲンカスタムの撃破':'Destroy the Falguen Custom',
 '敵戦艦の全滅':'Destroy all enemy warships', '衛星砲に注意':'Watch for the satellite cannon', '一定時間経過':'Hold out for the set time',
 '迎撃部隊の壊滅に注意':'Watch for interceptor losses', 'ミサイルが出現':'Missiles sighted', 'ミサイルには迎撃部隊が対応':'Interceptors handle the missiles',
 '迎撃部隊の増援が出現':'Interceptor reinforcements', 'ゴーストが出現':'Ghost sighted', '迎撃部隊の被害が拡大':'Interceptor losses mounting',
 '迎撃部隊が全て壊滅':'All interceptors lost', 'マクロスの撃破':'Destroy the Macross', 'ブラックメールの撃破':'Destroy the Blackmail',
 'バルチャー艦が敵対':'Vulture ship turned hostile', 'バルチャーが撤退':'Vultures retreating', 'バルチャーが降伏':'Vultures surrendered',
 '透明化に注意':'Watch for cloaking', 'バルチャーが協力':'Vultures cooperating', 'バルチャー艦を撃破しろ':'Destroy the Vulture ship',
 'ターゲット拠点の全制圧':'Capture all target bases', '友軍の増援が出現':'Allied reinforcements', '制御施設が陥落':'Control facility lost',
 '新型機がパワーダウン':'New unit losing power', '制御施設の制圧':'Control facility captured', '新型機がパワーアップ':'New unit powered up',
 '新型機が友軍戦艦を守るために進軍開始':'New unit moving to guard our ships', '新型機と協力して作戦を遂行しろ':'Work with the new unit',
 '制御施設を奪還しろ':'Retake the control facility', 'エリゴルカスタムの撃破':'Destroy the Eligor Custom', '戦艦を護衛する機体に注意':'Watch for warship escorts',
 '７隻の敵戦艦が領域を離脱':'7 enemy warships escaped', '敵戦艦の撃退':'Enemy warships repelled', '敵戦艦が領域を離脱':'Enemy warship escaped',
 '敵戦艦が離脱ラインに接近':'Enemy warship near escape line', '敵が防衛ラインに接近':'Enemy nearing defense line', '敵の防衛ライン突破':'Defense line breached',
 '敵の防衛ライン突破阻止':'Hold the defense line', '防衛ラインの突破阻止に成功':'Defense line held', 'ドミネーターの撃破':'Destroy the Dominator',
 '自走兵器のエネルギーチャージに注意':'Watch the mobile weapon charge', '自走兵器に接近して砲撃を阻止しろ':'Close in to stop the mobile weapon',
 '自走兵器がチャージを中止':'Mobile weapon stopped charging', '自走兵器による被害拡大':'Mobile weapon damage mounting',
 'プラネッタのオーバースキルが解除':"Planetta's Overskill cancelled", '拠点および自走兵器の制圧':'Base and mobile weapon captured',
 'プラネッタとの戦闘を避けろ':'Avoid fighting the Planetta', '障害エリアの解除':'Interference area cleared', '拠点を制圧すればジャミングが解除される':'Take the base: ends interference',
 'ゾンダーエプタの制圧':'Capture Zonder Epta', '粒子フィールドの解除':'Particle field down', '拠点の陥落':'Base lost',
 'ガンダムヴァサーゴが移動を開始':'Gundam Virsago on the move', 'ガンダムアシュタロンが移動を開始':'Gundam Ashtaron on the move',
 'ガンダムヴァサーゴが拠点に帰還':'Virsago back at its base', 'ガンダムアシュタロンが拠点に帰還':'Ashtaron back at its base',
 '周辺の拠点を制圧しろ':'Capture the nearby bases', '拠点の防衛':'Defend the base', '拠点の全制圧':'All bases captured', '拠点の防衛に成功':'Base defended',
 '粒子フィールドを解除':'Particle field down', '修復部隊の到着':'Repair team has arrived', 'フレイル部隊のＡＰが回復':"Flail team's AP restored",
 'グレイブアークの撃破':'Destroy the Grave Ark', '真ドラゴンの撃破':'Destroy Shin Dragon', 'インベーダーを撃破しろ':'Destroy the Invaders',
 '攻撃範囲から退避しろ':'Get out of the attack range', '真ドラゴンが弱体化':'Shin Dragon weakened', '真ドラゴンが行動再開':'Shin Dragon active again',
 '真ドラゴンとの交戦を避けろ':'Avoid engaging Shin Dragon', '敵を１００機撃墜':'Destroy 100 enemies', '敵を２０機撃墜':'20 enemies destroyed',
 '敵を４０機撃墜':'40 enemies destroyed', '敵を６０機撃墜':'60 enemies destroyed', '敵を８０機撃墜':'80 enemies destroyed',
 'オーバーデビルの撃破':'Destroy the Overdevil', '東側のターゲットを優先しろ':'Take the eastern targets first', '西からターゲットが接近中':'Targets coming from the west',
 '月光号が進軍を開始':'Gekko advancing', 'ナデシコＣの目標地点到達':'Nadesico C reaches its goal', '敵部隊の防衛ライン突破':'Defense line breached',
 '敵艦からの増援に注意':'Watch enemy ship launches', 'ＧビットはナデシコＣを攻撃しない':'G-Bits do not attack the Nadesico C',
 '敵戦艦から増援が出現':'Enemy warships launching units', '新たな敵戦艦が出現':'New enemy warship sighted',
 '各母艦を目標地点まで到達させろ':'Get every mothership to its goal', '月光号を目標地点まで到達させろ':'Get the Gekko to its goal',
 '友軍をコーラリアン出現地点まで誘導しろ':'Lead allies to the Coralian site', '友軍部隊が敵の足止めに成功':'Allies are holding the enemy',
 '抗体コーラリアンの出現が停止':'Antibody Coralians have stopped', '友軍の進路を確保しろ':"Clear the allies' route",
 'ナデシコＣを目標地点まで到達させろ':'Get the Nadesico C to its goal', '自走兵器を制圧しろ':'Suppress the mobile weapons', '自走兵器の制圧':'Mobile weapon suppressed',
 'ナデシコＣが進軍を開始':'Nadesico C advancing', 'ナデシコＣが目標地点に到達':'Nadesico C has reached its goal', 'タワーを目標地点まで到達させろ':'Get the Tower to its goal',
 '拠点を制圧しろ':'Capture the base', 'タワーが進軍を開始':'Tower advancing', '拠点部隊の増援が出現':'Base reinforcements', 'タワーが目標地点に到達':'Tower has reached its goal',
 '防護部隊が月光号に向けて進軍開始':'Escort team moving to the Gekko', '防護部隊がナデシコＣに向けて進軍開始':'Escort team moving to Nadesico C',
 '防護部隊がタワーに向けて進軍開始':'Escort team moving to the Tower', 'ナデシコＣのＡＰが回復':"Nadesico C's AP restored", 'タワーのＡＰが回復':"Tower's AP restored",
 '抗体コーラリアンが大量に発生':'Antibody Coralians swarming', '足止めのために友軍が進軍を開始':'Allies moving to hold the enemy',
 '母艦の目的地点到達':'Mothership reaches its goal', '大型タイプの抗体コーラリアンを優先しろ':'Large Antibody Coralians first',
 'ヤクト・ドーガ（クェス）の撃破':'Destroy the Jagd Doga (Quess)', '敵部隊が撤退':'Enemy forces retreating', '艦隊損害率が限界':'Fleet losses critical',
 'サザビーの撃破':'Destroy the Sazabi', '真ドラゴンの本体を攻撃しろ':"Attack Shin Dragon's body", '真ドラゴンの頭部を攻撃しろ':"Attack Shin Dragon's head",
 '母艦の目標地点到達':'Mothership reaches its goal', '自走兵器のチャージ率　７０％':'Mobile weapon charge at 70％',
 '艦隊損害率　２５％':'Fleet losses at 25％', '艦隊損害率　５０％':'Fleet losses at 50％', '艦隊損害率　７５％':'Fleet losses at 75％',
}


def norm(text):
    return text.replace('　', ' ').strip()


BODY_N = {norm(k):v for k, v in BODY.items()}
TEMPLATE = re.compile('^(.+?) ?(ダメージ|壊滅|全滅)(?: ?(\d+)％)?$|^(.+?)の(撃沈)$')


def translate(text):
    """One label. Returns None when a body is unknown."""
    text = norm(text)
    cat, sep, rest = text.partition('： ')
    prefix, body = (CATEGORY[cat]+': ', rest) if sep and cat in CATEGORY else ('', text)
    if body in BODY_N: return prefix+BODY_N[body]
    m = TEMPLATE.match(body.translate(FW))
    if m:
        name = (m.group(1) or m.group(4)).strip(); state = m.group(2) or m.group(5); pct = m.group(3)
        if name in NAMES:
            en = STATE[state] % (pct+'％') if pct else STATE[state]
            return prefix+NAMES[name]+' '+en
    return None


def labels():
    return {int(k):{int(i):v for i, v in d.items()} for k, d in json.loads(OUT.read_text(encoding='utf-8'))['scenes'].items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    out, unknown = {}, []
    with (ROOT/'work/output/ACE3-English-0.1.30.iso').open('rb') as f:
        fi, es = archive(f); ids = {e[3]:e for e in es}
        for x in range(8, 36):
            rid = 2002000+x*10; e = ids[rid]; f.seek(fi['offset']+e[2]); d = f.read(e[1]); out[rid] = {}
            for _, i, _, raw in parse_table(d, u32(d, 20))[3]:
                text = raw.decode('cp932')
                if b'<sp(' in raw or not JP.search(text): continue
                en = translate(text)
                if en is None: unknown.append((rid, i, text)); continue
                require(not re.search('[jq]', en.replace('Objective', '').replace('Jagd', '')), 'j/q glyph in '+en)
                out[rid][i] = en
    print('labels', sum(len(v) for v in out.values()), 'unknown', len(unknown))
    for u in unknown: print('UNKNOWN', u)
    if not a.write: return
    require(not unknown, 'Unresolved labels')
    OUT.write_text(json.dumps({'note':'HUD labels for live scenes 2002080-2002350; wording follows the 0.1.21 labels', 'scenes':out}, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
