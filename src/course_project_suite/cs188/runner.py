from __future__ import annotations
from course_project_suite.common import CheckResult, make_classification, accuracy, set_seed, train_val_split
from .pacman_core import parse_layout, TINY_LAYOUT
from .search import PositionSearchProblem, CornersProblem, breadth_first_search, a_star_search, corners_heuristic
from .multiagent import AlphaBetaAgent
from .rl import GridMDP, value_iteration, QLearningAgent
from .inference import forward_filter, viterbi
from .ml import PerceptronClassifier

def run():
    set_seed(1)
    game=parse_layout(TINY_LAYOUT)
    food=next(iter(game.food))
    path=breadth_first_search(PositionSearchProblem(game, food))
    corners=((1,1),(5,1),(1,3),(5,3))
    cpath=a_star_search(CornersProblem(game,corners), corners_heuristic)
    action=AlphaBetaAgent(depth=1).get_action(game)
    V,pol=value_iteration(GridMDP(),iterations=20)
    states=['H','C']; obs=['walk','shop','clean']; start={'H':.6,'C':.4}; trans={'H':{'H':.7,'C':.3},'C':{'H':.4,'C':.6}}; emit={'H':{'walk':.6,'shop':.3,'clean':.1},'C':{'walk':.1,'shop':.4,'clean':.5}}
    filtered=forward_filter(obs,states,start,trans,emit); seq,_=viterbi(obs,states,start,trans,emit)
    X,y=make_classification(n=150,d=5,c=3,seed=3); X_train,X_val,y_train,y_val=train_val_split(X,y,val_fraction=.25,seed=3)
    clf=PerceptronClassifier(5,3,epochs=6).fit(X_train,y_train); acc=accuracy(clf.predict(X_val),y_val)
    metrics={'bfs_len':len(path),'corners_astar_len':len(cpath),'alpha_beta_action':action,'mdp_start_value':round(V[(0,2)],3),'hmm_final_cold_prob':round(filtered[-1]['C'],3),'viterbi':'-'.join(seq),'perceptron_val_acc':acc}
    ok=len(path)>0 and action in game.legal_actions(0) and abs(sum(filtered[-1].values())-1)<1e-9 and acc>0.85
    return CheckResult('cs188_pacman_projects_public_alignment', ok, metrics)
