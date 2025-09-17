# gen_dataset.py
import csv, time, random
WIN = [(0,0,0,1,1,1,2,2,2),(0,1,2,0,1,2,0,1,2),(0,1,2,0,1,2,0,1,2)]  # placeholder

WIN_LINES = [
    [(0,0),(0,1),(0,2)],[(1,0),(1,1),(1,2)],[(2,0),(2,1),(2,2)],
    [(0,0),(1,0),(2,0)],[(0,1),(1,1),(2,1)],[(0,2),(1,2),(2,2)],
    [(0,0),(1,1),(2,2)],[(0,2),(1,1),(2,0)]
]
def empty(b): return [(i,j) for i in range(3) for j in range(3) if b[i][j]==0]
def wins(b,p): return any(all(b[i][j]==p for i,j in L) for L in WIN_LINES)
def over(b): return wins(b,1) or wins(b,-1) or not empty(b)
def evalb(b,ai): return 1 if wins(b,ai) else (-1 if wins(b,-ai) else 0)

def minimax_ab(b, depth, cur, ai, a, bt):
    if depth==0 or over(b): return (-1,-1, evalb(b,ai)*(10+depth))
    best = (-1,-1,-10_000) if cur==ai else (-1,-1,10_000)
    for (i,j) in empty(b):
        b[i][j]=cur
        _,_,s=minimax_ab(b, depth-1, -cur, ai, a, bt); b[i][j]=0
        if cur==ai:
            if s>best[2]: best=(i,j,s); a=max(a,s)
        else:
            if s<best[2]: best=(i,j,s); bt=min(bt,s)
        if bt<=a: break
    return best

def ai_move(b, ai, diff):
    params={"easy":(0.6,1,False),"normal":(0.2,3,False),"hard":(0.05,9,True),"impossible":(0.0,9,True)}
    p_rand, depth_lim, use_center = params[diff]
    E = empty(b); d=len(E)
    if E and random.random()<p_rand: i,j=random.choice(E); b[i][j]=ai; return
    if use_center and d==9 and b[1][1]==0: b[1][1]=ai; return
    eff=min(d, depth_lim)
    if eff==0: i,j=E[0]; b[i][j]=ai; return
    i,j,_=minimax_ab(b, eff, ai, ai, -10_000, 10_000)
    if i==-1: i,j=E[0]
    b[i][j]=ai

def rnd_move(b,p):
    E=empty(b)
    if E: i,j=random.choice(E); b[i][j]=p

def opt_move(b,p):
    i,j,_=minimax_ab(b, len(empty(b)), p, p, -10_000, 10_000)
    if i==-1:
        E=empty(b);
        if not E: return
        i,j=E[0]
    b[i][j]=p

def play(diff, opponent, ai_starts, seed=None):
    if seed is not None: random.seed(seed)
    b=[[0]*3 for _ in range(3)]
    ai=+1; turn=bool(ai_starts); moves=0
    while not over(b):
        t0=time.time()
        if turn: ai_move(b, ai, diff)
        else: opt_move(b,-ai) if opponent=="optimal" else rnd_move(b,-ai)
        t1=time.time(); moves+=1
        turn=not turn
    res=1 if wins(b,ai) else (-1 if wins(b,-ai) else 0)
    return res, moves, t1

import csv, os, tempfile, time

def gen_csv(out_path, opponent, N, difficulties=("easy","normal","hard","impossible"), seed_base=None):
    rows = []
    gid = 0
    for diff in difficulties:
        for i in range(N):
            ai_starts = (i % 2 == 0)
            seed = None if seed_base is None else (seed_base + gid)
            res, mv, ts = play(diff, opponent, ai_starts=ai_starts, seed=seed)  # dùng hàm play sẵn có
            rows.append([gid, diff, opponent, int(ai_starts), res, mv, int(time.time())])
            gid += 1

    dir_ = os.path.dirname(out_path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".tmp_", suffix=".csv")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["game_id","difficulty","opponent","ai_starts","result","moves","timestamp"])
        w.writerows(rows)
    os.replace(tmp, out_path)  # ghi đè file cũ


gen_csv("../datasets/dataset1_random.csv", "random", 200, seed_base=1000)
gen_csv("../datasets/dataset2_optimal.csv", "optimal", 40, seed_base=5000)

