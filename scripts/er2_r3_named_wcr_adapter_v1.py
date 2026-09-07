from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import csv
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import numpy as np
import pandas as pd

import econometric_design_master_v1 as ed1

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'scripts/er2_r3_named_wcr_adapter_v1.py'
TEST = 'tests/test_er2_r3_named_wcr_adapter_v1.py'
CSV = 'outputs/econometrics/ER2_R3A_ADAPTER_VALIDATION.csv'
REPORT = 'outputs/econometrics/ER2_R3A_ADAPTER_VALIDATION_REPORT.md'
LOCK = 'outputs/econometrics/ER2_R3A_ADAPTER_LOCK.json'
CANDIDATES = (SCRIPT, TEST, CSV, REPORT, LOCK)
PARENT = '611c91255d5a367127df57dd69855e2df83ac0cb'
BRANCH = 'phase/er2-r2-standardized-anomaly-v1'
TAG = 'er2-r2-standardized-anomaly-v1-freeze'
ER2P = '3fd1f657e79d7e0ae93903239fd3690dcade56a4'
TIER_SHA = 'a70eb6398e9073053fd619fc985e9f8e3348be42bc0212f42d99dde475fa0864'
CERT_SHA = 'a37ba8ee9fdebe400b638404200d1109fa3045c59ec2b1f6c76b35c3cc3284a4'
INITIAL_SHA = '117a3fe5da88f44d31b176495409f6e84189148f1020417f046b0df3dd4c5f6b'
ED1_SHA = '69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195'
CONTRACTS = 'outputs/econometrics/ED1_MODEL_CONTRACTS.csv'
TIERS = 'outputs/econometrics/ER2P_TIER_CONTRACTS.csv'
PROTOCOL = 'config/econometrics/er2_robustness_protocol_v1.json'
METADATA = {
    CONTRACTS:'7dcd316c7b47b3a2e15939ed25dea8e034f1ca7c5076013c7640ef11da74cbcf',
    TIERS:'2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a',
    PROTOCOL:'13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff',
    'scripts/econometric_design_master_v1.py':ED1_SHA,
}
SYNTHETIC_SPEC = {
    'schema':'ER2_R3A_SYNTHETIC_PANEL_V1', 'data_seed':2026090501,
    'rng':'NUMPY_GENERATOR_PCG64', 'clusters':16, 'periods':8,
    'architecture_sizes':[3,6], 'beta':[0.10,-0.20,0.35,-0.50,0.75,-0.90],
    'x_common_loading':0.25, 'noise_ar1':0.55, 'cluster_time_slope_scale':0.30,
    'district_fe_scale':0.40, 'period_fe_scale':0.20,
    'bootstrap_seed':20260903, 'bootstrap_replications':2001, 'batch_size':1000,
    'absolute_tolerance':1e-10, 'relative_tolerance':1e-10,
    'exact_observed_statistic_gate':True,
    'reference':'ORIGINAL_ORDER_ONE_HOT_KKT_RESTRICTED_OLS_INDEPENDENT_FULL_DESIGN_CR2',
    'generator_order':'NEW_SEEDED_GENERATOR_PER_ARCHITECTURE_X_COMMON_CLUSTER_AR_NOISE_PERIOD',
}
PASS = 'ER2_R3A_PASS_NAMED_COEFFICIENT_ADAPTER_VALIDATED_READY_FOR_FREEZE_DECISION'
HOLD = 'ER2_R3A_HOLD_CONTRAST_PERMUTATION_DISAGREEMENT'
INVALID = 'ER2_R3A_HOLD_INVALID_SYNTHETIC_REPLICATIONS'
REAL_FAIL = 'ER2_R3A_FAIL_REAL_OUTCOME_FIREWALL'
NEXT = 'RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3A_FREEZE_DECISION_IF_PASS'


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)+'\n').encode('utf-8')


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def array_sha(value):
    return sha(np.asarray(value,dtype='<f8').tobytes())


def git(*args):
    return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)


def preflight():
    if git('rev-parse','HEAD').decode().strip() != PARENT:
        raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: parent')
    for ref in ('refs/heads/'+BRANCH,'refs/remotes/origin/'+BRANCH,'refs/tags/'+TAG+'^{}'):
        if git('rev-parse',ref).decode().strip() != PARENT:
            raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: R2 ref')
    if git('rev-parse','phase/er2p-robustness-protocol-v1').decode().strip() != ER2P:
        raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: ER2P')
    if git('diff','--name-only','HEAD').strip():
        raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: tracked change')
    unknown = set(git('ls-files','--others','--exclude-standard').decode().splitlines())-set(CANDIDATES)
    if unknown:
        raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: unexpected candidate')
    for p,h in METADATA.items():
        if sha((ROOT/p).read_bytes()) != h or sha(git('cat-file','blob',PARENT+':'+p)) != h:
            raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: metadata')
    # Locks are opaque hash inputs only: their real estimates are never parsed.
    for p,h in [('outputs/econometrics/ER2_R2_RESULTS_LOCK_REPORTING_CERTIFIED.json',CERT_SHA),
                ('outputs/econometrics/ER2_R2_RESULTS_LOCK.json',INITIAL_SHA)]:
        if sha(git('cat-file','blob',PARENT+':'+p)) != h:
            raise RuntimeError('ER2_R3A_FAIL_UPSTREAM_IMMUTABILITY: lock')
    tier = next(r for r in json.loads((ROOT/PROTOCOL).read_bytes())['tiers'] if r['tier']=='R3')
    if sha(json_bytes(tier)) != TIER_SHA:
        raise RuntimeError('ER2_R3A_FAIL_TARGET_MAP: tier hash')
    row = next(r for r in csv.DictReader(io.StringIO((ROOT/TIERS).read_text(encoding='utf-8'))) if r['ORDER']=='3')
    expected = {'TIER':'R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP','ROLE':'INFERENCE_ONLY',
                'FAMILY':'PHYSICAL_ANOMALY','MULTIPLICITY':'WITHIN_CROP_WCR_COEFFICIENT_P_VALUES',
                'PREVIOUS_TIER':'R2','NEXT_TIER':'R4','TIER_CONTRACT_SHA256':TIER_SHA}
    if any(row[k] != v for k,v in expected.items()):
        raise RuntimeError('ER2_R3A_FAIL_TARGET_MAP: tier metadata')
    if (tier['seed'],tier['replications'],tier['determinism']['batch_size']) != (20260903,9999,1000):
        raise RuntimeError('ER2_R3A_FAIL_TARGET_MAP: future contract')
    return {'parent':PARENT,'er2p':ER2P,'r2_reporting_lock_sha256':CERT_SHA,
            'r2_initial_lock_sha256':INITIAL_SHA,'r3_tier_contract_sha256':TIER_SHA,
            'metadata_sha256':METADATA,'future_real_contract':tier}


def permutation(x_columns, target_variable):
    cols = list(x_columns)
    if not cols or len(set(cols)) != len(cols) or target_variable not in cols:
        raise ValueError('Unique regressor names and one present target required')
    j = cols.index(target_variable)
    order = [j]+[i for i in range(len(cols)) if i != j]
    inverse = np.argsort(order).tolist()
    return j, order, inverse


def target_map():
    rows = list(csv.DictReader(io.StringIO((ROOT/CONTRACTS).read_text(encoding='utf-8'))))
    if [int(r['CLIMATE_COEFFICIENT_COUNT']) for r in rows] != [3,3,3,6,6]:
        raise RuntimeError('ER2_R3A_FAIL_TARGET_MAP')
    mapped = []
    for row in rows:
        cols = row['PRIMARY_REGRESSORS'].split('|')
        for variable in cols:
            j,order,inverse = permutation(cols,variable)
            mapped.append({'CROP':row['CROP'],'CROP_CODE':row['CROP_CODE'],'VARIABLE':variable,
                           'FROZEN_POSITION':j,'ARCHITECTURE':len(cols),'PERMUTATION':order,
                           'INVERSE_PERMUTATION':inverse,'FROZEN_REGRESSORS':cols,
                           'FROZEN_WINDOWS':row['WINDOW_IDS'].split('|'),
                           'REAL_OUTCOME_EXECUTION_STATUS':'NOT_EXECUTED'})
    if len(mapped) != 21 or len({(r['CROP_CODE'],r['VARIABLE']) for r in mapped}) != 21:
        raise RuntimeError('ER2_R3A_FAIL_TARGET_MAP')
    return mapped


class RealOutcomeFirewall(RuntimeError):
    pass


_GUARD_ACTIVE = 0
_GUARD_BLOCKED = 0
_HOOK_INSTALLED = False


def _file_firewall(event,args):
    global _GUARD_BLOCKED
    if event != 'open' or not _GUARD_ACTIVE or not isinstance(args[0],(str,bytes,os.PathLike)):
        return
    path = Path(os.fsdecode(args[0])).absolute()
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        return
    blocked = rel.startswith('data/') or (rel.startswith('outputs/') and rel not in (CONTRACTS,TIERS,CSV,REPORT,LOCK))
    if blocked:
        _GUARD_BLOCKED += 1
        raise RealOutcomeFirewall(REAL_FAIL+': repository data/result read blocked')


def deny_real_loader(*args,**kwargs):
    raise RealOutcomeFirewall(REAL_FAIL+': real loader blocked')


@contextmanager
def outcome_firewall():
    global _GUARD_ACTIVE, _HOOK_INSTALLED
    if not _HOOK_INSTALLED:
        sys.addaudithook(_file_firewall)
        _HOOK_INSTALLED = True
    _GUARD_ACTIVE += 1
    try:
        with patch.object(ed1,'read_transient_primary',deny_real_loader), \
             patch.object(ed1,'read_perennial_primary',deny_real_loader), \
             patch.object(ed1,'read_b3_sensitivity',deny_real_loader):
            yield
    finally:
        _GUARD_ACTIVE -= 1


def synthetic_panel(columns):
    s = SYNTHETIC_SPEC
    rng = np.random.Generator(np.random.PCG64(s['data_seed']))
    g,t = s['clusters'],s['periods']
    k = len(columns)
    x = rng.normal(size=(g,t,k)) + s['x_common_loading']*rng.normal(size=(g,t,1))
    district = rng.normal(size=g)
    slopes = rng.normal(size=g)*s['cluster_time_slope_scale']
    innovations = rng.normal(size=(g,t))
    errors = innovations.copy()
    for period in range(1,t):
        errors[:,period] += s['noise_ar1']*errors[:,period-1]
    periods = np.arange(t,dtype=float)
    noise = errors + slopes[:,None]*(periods-periods.mean())
    period_fe = rng.normal(size=t)*s['period_fe_scale']
    y = x@np.asarray(s['beta'][:k]) + s['district_fe_scale']*district[:,None] + period_fe + noise
    frame = pd.DataFrame(x.reshape(g*t,k),columns=columns)
    frame['UBIGEO'] = np.repeat([f'SYNTHETIC_{i:03d}' for i in range(g)],t)
    frame['PERIOD'] = np.tile(np.arange(t),g)
    return frame,y.ravel()


def finite_p(exceedances,replications):
    if not isinstance(exceedances,int) or not isinstance(replications,int) or replications < 1 or not 0 <= exceedances <= replications:
        raise ValueError('Invalid bootstrap counts')
    return (1+exceedances)/(replications+1)


def tier_status(invalid_replications):
    return 'HOLD' if invalid_replications != 0 else 'COMPLETE'


def frozen_wcr_audit(frame,columns,period,response,replications,seed,restriction):
    function = ed1.restricted_wild_cluster_bootstrap_t
    source,start = inspect.getsourcelines(function)
    batch_line = start+next(i for i,line in enumerate(source) if line.strip()=='completed += count')
    batches, captured = [], {}
    previous = sys.gettrace()
    def trace(current,event,arg):
        if current.f_code is not function.__code__:
            return None
        state = current.f_locals
        if event=='line' and current.f_lineno==batch_line:
            batches.append({'draws':state['cluster_weights'].copy(),'statistics':state['statistics'].copy(),
                            'count':state['count'],'rng_state':state['rng'].bit_generator.state})
        elif event=='return':
            captured.update({k:state[k] for k in ('fit','observed_statistic','exceedances','invalid','restricted_residual','beta_null') if k in state})
        return trace
    try:
        sys.settrace(trace)
        result = function(frame,columns,period,response,replications,seed,restriction_kind=restriction)
    finally:
        sys.settrace(previous)
    if not captured or sum(b['count'] for b in batches) != replications:
        raise RuntimeError('Frozen WCR audit capture incomplete')
    captured.update(frozen_result=result,batches=batches,
                    exact_p=finite_p(int(captured['exceedances']),replications),
                    invalid_replications=int(captured.pop('invalid')))
    return captured


def named_coefficient_wcr_adapter(frame,x_columns,period_column,response,target_variable,
                                  replications=9999,seed=20260903,batch_size=1000):
    j,order,inverse = permutation(x_columns,target_variable)
    if batch_size != 1000 or not isinstance(replications,int) or replications < 1:
        raise ValueError('Frozen ED1 batch size is 1000 and B must be positive')
    if frame[['UBIGEO',period_column]].duplicated().any():
        raise ValueError('Duplicate district-period rows')
    if not frame[['UBIGEO',period_column]].equals(frame.sort_values(['UBIGEO',period_column],kind='mergesort')[['UBIGEO',period_column]]):
        raise ValueError('Rows must already be sorted; adapter never reorders Y')
    if np.asarray(response).ndim != 1 or len(response) != len(frame) or not np.isfinite(np.asarray(response)).all() or not np.isfinite(frame[list(x_columns)].to_numpy()).all():
        raise ValueError('Finite aligned synthetic response and complete X required')
    columns = [x_columns[i] for i in order]
    result = frozen_wcr_audit(frame,columns,period_column,response,replications,seed,'FIRST_CLIMATE_COEFFICIENT')
    return {'target_variable':target_variable,'original_position':j,'permutation':order,
            'inverse_permutation':inverse,'target_position':0,'regressors':columns,
            'frozen_wcr_result':result['frozen_result'],'audit':result,
            'invalid_replications':result['invalid_replications'],
            'tier_status':tier_status(result['invalid_replications']),
            'determinism':{'rng':'NUMPY_GENERATOR_PCG64','seed':seed,'replications':replications,
                           'batch_size':batch_size,'cluster_order':'SORTED_UBIGEO',
                           'row_order':'SORTED_UBIGEO_THEN_FROZEN_PERIOD',
                           'seed_reset':'EACH_CROP_CONTRAST_AND_JOINT_TEST','weights':'RADEMACHER'}}


def one_hot_reference(frame,columns,period,response,target,replications,seed):
    # Independent full-design OLS/CR2 and KKT null restriction, in original column order.
    labels = frame['UBIGEO'].astype(str).to_numpy()
    periods = frame[period].astype(str).to_numpy()
    clusters = sorted(set(labels))
    fe = np.column_stack([np.ones(len(frame))]+[(labels==v).astype(float) for v in clusters[1:]]+
                         [(periods==v).astype(float) for v in sorted(set(periods))[1:]])
    design = np.column_stack([fe,frame[columns].to_numpy(float)])
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise ValueError('Reference design rank failure')
    gram = design.T@design
    bread = np.linalg.inv(gram)
    beta = np.linalg.solve(gram,design.T@response)
    residual = response-design@beta
    projection = np.eye(len(frame))-design@bread@design.T
    projection = (projection+projection.T)/2
    groups = [np.flatnonzero(labels==g) for g in clusters]
    adjustments,scores = [],[]
    for idx in groups:
        block = projection[np.ix_(idx,idx)]
        values,vectors = np.linalg.eigh((block+block.T)/2)
        threshold = np.finfo(float).eps*len(idx)*max(1.,np.max(np.abs(values)))*128
        positive = values>threshold
        if positive.sum() != len(idx)-1 or values.min() < -threshold:
            raise ValueError('Reference CR2 structural rank failure')
        adjustment = (vectors[:,positive]/np.sqrt(values[positive]))@vectors[:,positive].T
        adjustments.append(adjustment)
        scores.append(design[idx].T@adjustment@residual[idx])
    covariance = bread@sum(np.outer(v,v) for v in scores)@bread
    contrast = np.zeros((1,design.shape[1]))
    contrast[0,fe.shape[1]+target] = 1
    kkt = np.block([[gram,contrast.T],[contrast,np.zeros((1,1))]])
    beta_null = np.linalg.solve(kkt,np.r_[design.T@response,0.])[:-1]
    restricted = response-design@beta_null
    observed = abs(float((contrast@beta)[0]/np.sqrt((contrast@covariance@contrast.T)[0,0])))
    rng = np.random.Generator(np.random.PCG64(seed))
    batches,exceedances,invalid = [],0,0
    for start in range(0,replications,1000):
        count = min(1000,replications-start)
        draws = rng.integers(0,2,size=(len(groups),count),dtype=np.int8).astype(float)*2-1
        weights = np.empty((len(frame),count))
        for i,idx in enumerate(groups):
            weights[idx] = draws[i]
        shock = restricted[:,None]*weights
        delta = np.linalg.solve(gram,design.T@shock)
        residual_star = shock-design@delta
        target_beta = (contrast@(beta_null[:,None]+delta))[0]
        variance = np.zeros(count)
        for idx,adjustment in zip(groups,adjustments):
            influence = contrast@bread@design[idx].T@adjustment@residual_star[idx]
            variance += influence[0]**2
        valid = np.isfinite(variance)&(variance>0)&np.isfinite(target_beta)
        statistics = np.full(count,np.nan)
        statistics[valid] = np.abs(target_beta[valid]/np.sqrt(variance[valid]))
        exceedances += int(np.sum(statistics[valid]>=observed))
        invalid += int((~valid).sum())
        batches.append({'draws':draws,'statistics':statistics,'count':count,'rng_state':rng.bit_generator.state})
    return {'fit':{'design':design,'full_beta':beta,'residual':residual,'covariance':covariance,
                   'fixed_effects':fe,'cluster_labels':clusters,'cluster_indices':groups},
            'observed_statistic':observed,'exceedances':exceedances,'invalid_replications':invalid,
            'restricted_residual':restricted,'beta_null':beta_null,'batches':batches,
            'exact_p':finite_p(exceedances,replications)}


def close(a,b):
    return bool(np.allclose(a,b,atol=SYNTHETIC_SPEC['absolute_tolerance'],rtol=SYNTHETIC_SPEC['relative_tolerance'],equal_nan=False))


def delta(a,b):
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))


def compare_paths(left,right,inverse=None):
    lf,rf = left['fit'],right['fit']
    mapping = np.arange(len(lf['full_beta']))
    if inverse is not None:
        offset = len(mapping)-len(inverse)
        mapping[offset:] = offset+np.asarray(inverse)
    lb = lf['full_beta'][mapping]
    lc = lf['covariance'][np.ix_(mapping,mapping)]
    fitted_l,fitted_r = lf['design']@lf['full_beta'],rf['design']@rf['full_beta']
    metrics = {'beta':delta(lb,rf['full_beta']),'fitted':delta(fitted_l,fitted_r),
               'residual':delta(lf['residual'],rf['residual']),
               'cr2_covariance':delta(lc,rf['covariance']),
               'observed_statistic':abs(left['observed_statistic']-right['observed_statistic']),
               'restricted_residual':delta(left['restricted_residual'],right['restricted_residual'])}
    numeric = (close(lb,rf['full_beta']) and close(fitted_l,fitted_r) and close(lf['residual'],rf['residual'])
               and close(lc,rf['covariance']) and close(left['observed_statistic'],right['observed_statistic'])
               and close(left['restricted_residual'],right['restricted_residual']))
    draws_equal = len(left['batches'])==len(right['batches']) and all(
        a['count']==b['count'] and np.array_equal(a['draws'],b['draws']) and a['rng_state']==b['rng_state']
        for a,b in zip(left['batches'],right['batches']))
    assignments = lf['cluster_labels']==rf['cluster_labels'] and all(np.array_equal(a,b) for a,b in zip(lf['cluster_indices'],rf['cluster_indices']))
    exact_observed = left['observed_statistic']==right['observed_statistic']
    counts = left['exceedances']==right['exceedances'] and left['invalid_replications']==right['invalid_replications']
    p_equal = left['exact_p']==right['exact_p']
    return {'numerical_tolerance_pass':numeric,'max_absolute_errors':metrics,'cluster_assignment_exact':assignments,
            'draws_rng_batches_exact':draws_equal,'observed_statistic_exact':exact_observed,
            'exceedances_invalid_exact':counts,'finite_p_exact':p_equal,
            'status':'PASS' if numeric and assignments and draws_equal and exact_observed and counts and p_equal else 'HOLD'}


def execution_summary(result):
    return {'observed_absolute_t_or_wald_f':result['observed_statistic'],
            'exceedances':int(result['exceedances']),'invalid_replications':result['invalid_replications'],
            'exact_finite_p':result['exact_p'],'batch_partition':[b['count'] for b in result['batches']],
            'draw_sha256':[array_sha(b['draws']) for b in result['batches']],
            'statistics_sha256':[array_sha(b['statistics']) for b in result['batches']],
            'final_pcg64_state':result['batches'][-1]['rng_state']}


def branch_audit():
    tree = ast.parse((ROOT/SCRIPT).read_text(encoding='utf-8'))
    nodes = {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    forbidden = ('BANANA','MANGO','LEMON','RAIN_ANOM','TMIN_ANOM','TMAX_ANOM','140100','13010','150100')
    findings = []
    for name in ('permutation','named_coefficient_wcr_adapter','frozen_wcr_audit'):
        for node in ast.walk(nodes[name]):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and any(v in node.value.upper() for v in forbidden):
                findings.append(name)
    reference_calls = [n.func.id for n in ast.walk(nodes['one_hot_reference']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
    if any(n in reference_calls for n in ('named_coefficient_wcr_adapter','frozen_wcr_audit')):
        raise RuntimeError('Independent reference calls adapter or permuted path')
    return {'result_specific_adapter_branches':len(findings),'reference_independence':'PASS' if not findings else 'FAIL'}


def validate():
    spec_bytes = json_bytes(SYNTHETIC_SPEC)
    pre = preflight()
    mapping = target_map()
    results,identities,joints = {},{},{}
    with outcome_firewall():
        for size in SYNTHETIC_SPEC['architecture_sizes']:
            columns = next(r['FROZEN_REGRESSORS'] for r in mapping if r['ARCHITECTURE']==size)
            frame,y = synthetic_panel(columns)
            other,other_y = synthetic_panel(columns)
            if not frame.equals(other) or not np.array_equal(y,other_y):
                raise RuntimeError('ER2_R3A_FAIL_DETERMINISM: synthetic generator')
            identities[str(size)] = {'x_sha256':array_sha(frame[columns].to_numpy()),'y_sha256':array_sha(y),
                                     'keys_sha256':sha(json_bytes(frame[['UBIGEO','PERIOD']].values.tolist())),
                                     'rows':len(frame),'data_generation_twice_exact':True}
            snapshot = frame.copy(deep=True),y.copy()
            b,seed = SYNTHETIC_SPEC['bootstrap_replications'],SYNTHETIC_SPEC['bootstrap_seed']
            for j,target in enumerate(columns):
                adapted = named_coefficient_wcr_adapter(frame,columns,'PERIOD',y,target,b,seed)
                path_a = adapted['audit']
                explicit = [columns[j]]+columns[:j]+columns[j+1:]
                path_b = frozen_wcr_audit(frame,explicit,'PERIOD',y,b,seed,'FIRST_CLIMATE_COEFFICIENT')
                path_c = one_hot_reference(frame,columns,'PERIOD',y,j,b,seed)
                ab,ac = compare_paths(path_a,path_b),compare_paths(path_a,path_c,adapted['inverse_permutation'])
                invalid = sum(p['invalid_replications'] for p in (path_a,path_b,path_c))
                state = INVALID if invalid else (PASS if ab['status']==ac['status']=='PASS' else HOLD)
                results[f'{size}:{j}'] = {'architecture':size,'position':j,'A':execution_summary(path_a),
                                         'B':execution_summary(path_b),'C':execution_summary(path_c),
                                         'A_B':ab,'A_C':ac,'verdict':state,'invalid_replications':invalid,
                                         'full_regressor_set_preserved':set(explicit)==set(columns) and len(explicit)==size,
                                         'frame_response_unchanged':frame.equals(snapshot[0]) and np.array_equal(y,snapshot[1])}
            joint_a = frozen_wcr_audit(frame,columns,'PERIOD',y,b,seed,'ALL_CLIMATE_COEFFICIENTS')
            order = list(reversed(range(size)))
            joint_b = frozen_wcr_audit(frame,[columns[i] for i in order],'PERIOD',y,b,seed,'ALL_CLIMATE_COEFFICIENTS')
            joint_check = compare_paths(joint_b,joint_a,np.argsort(order).tolist())
            joints[str(size)] = {'original':execution_summary(joint_a),'permuted':execution_summary(joint_b),'comparison':joint_check}
    audit = branch_audit()
    invalid_total = sum(r['invalid_replications'] for r in results.values())+sum(j[p]['invalid_replications'] for j in joints.values() for p in ('original','permuted'))
    validated = all(r['verdict']==PASS for r in results.values()) and all(j['comparison']['status']=='PASS' for j in joints.values())
    verdict = INVALID if invalid_total else (PASS if validated and audit['result_specific_adapter_branches']==0 else HOLD)
    preflight()
    return {'schema_version':'1.0.0','gate':'ER2_R3A_NAMED_COEFFICIENT_WCR_ADAPTER_VALIDATION_V1',
            'project':'ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA','preflight':pre,
            'implementation_sha256':sha((ROOT/SCRIPT).read_bytes()),'test_sha256':sha((ROOT/TEST).read_bytes()),
            'synthetic_specification':SYNTHETIC_SPEC,'synthetic_specification_sha256':sha(spec_bytes),
            'synthetic_identities':identities,'target_map':mapping,'positional_validation':results,
            'joint_validation':joints,'invalid_replications':invalid_total,'branch_audit':audit,
            'R3_ADAPTER_VALIDATED':verdict==PASS,'ALL_TARGET_POSITIONS_VALIDATED':validated,
            'ALL_TARGET_POSITIONS_TESTED':sorted(results),'REAL_OUTCOME_VALUES_READ':False,
            'REAL_R3_EXECUTED':False,'REAL_R3_MODELS_EXECUTED':0,'REAL_BOOTSTRAP_REPLICATIONS_EXECUTED':0,
            'PRIMARY_RESULTS_VALUES_COPIED':False,'R2_RESULTS_VALUES_COPIED':False,
            'INVALID_REPLICATION_FIREWALL':'HOLD_NO_DROP_NO_REDRAW_NO_DENOMINATOR_CHANGE',
            'finite_correction_edges':{'zero':finite_p(0,2001),'all':finite_p(2001,2001)},
            'R3_MULTIPLICITY':'HOLM_STEP_DOWN_WITHIN_CROP_WCR_COEFFICIENT_P_VALUES',
            'holm_family_sizes':[3,3,3,6,6],'real_holm_calculated':False,
            'NEXT_TIER_AUTHORIZATION_STATUS':'NOT_AUTHORIZED','R4':'NOT_EXECUTED','R5':'NOT_EXECUTED','R6':'NOT_EXECUTED',
            'final_verdict':verdict,'next_action':NEXT}


def csv_bytes(rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def render(data,reproduction):
    rows = []
    for target in data['target_map']:
        v = data['positional_validation'][f"{target['ARCHITECTURE']}:{target['FROZEN_POSITION']}"]
        row = {k:('|'.join(map(str,value)) if isinstance(value,list) else value) for k,value in target.items()}
        row.update(SYNTHETIC_POSITIONAL_VALIDATION=v['verdict'],A_B_STATUS=v['A_B']['status'],
                   A_C_STATUS=v['A_C']['status'],A_C_OBSERVED_EXACT=v['A_C']['observed_statistic_exact'],
                   A_C_OBSERVED_ABS_ERROR=v['A_C']['max_absolute_errors']['observed_statistic'],
                   INVALID_REPLICATIONS=v['invalid_replications'])
        rows.append(row)
    report = ['# ER2 R3A Named-Coefficient WCR Adapter Validation v1','',
              'SYNTHETIC DATA ONLY. No real outcomes or real R3 execution.','',
              'VERDICT = '+data['final_verdict'],'',
              '## Prespecified synthetic design','',
              'Seed 2026090501; 16 synthetic districts x 8 periods; three- and six-regressor full models.',
              'Unequal fixed coefficients, district/period FE, AR(1) synthetic noise and district-specific time slopes.',
              'Specification SHA-256: '+data['synthetic_specification_sha256'],
              'B=2001; PCG64 seed=20260903; Rademacher batches=1000+1000+1; atol=rtol=1e-10.',
              'The exact observed-statistic gate is separate from the tolerance diagnostic. No rounding to manufacture equivalence.','',
              '## Three independent paths','',
              'A: named permutation adapter. B: explicit permutation and frozen ED1 first-coefficient API.',
              'C: original-order one-hot KKT restriction, independent full-design OLS/CR2 bootstrap.',
              'Read-only frame tracing captures the frozen engine counts and draws; no RNG calls are inserted.',
              'The original rounded ED1 p-value is preserved in the adapter API; exact finite p uses captured integer counts.','',
              '## Positional certification','',
              '| Size | Position | A/B | A/C | A/C t exact | A/C t absolute error | Exceedances A/B/C |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for key,v in data['positional_validation'].items():
        report.append(f"| {v['architecture']} | {v['position']} | {v['A_B']['status']} | {v['A_C']['status']} | {v['A_C']['observed_statistic_exact']} | {v['A_C']['max_absolute_errors']['observed_statistic']} | {v['A']['exceedances']}/{v['B']['exceedances']}/{v['C']['exceedances']} |")
    report += ['', '## Joint noninterference','']
    for size,j in data['joint_validation'].items():
        report.append(f"Architecture {size}: {j['comparison']['status']}; observed exact={j['comparison']['observed_statistic_exact']}; error={j['comparison']['max_absolute_errors']['observed_statistic']}; p exact={j['comparison']['finite_p_exact']}.")
    report += ['', '## Firewalls and reproducibility','',
               'Invalid synthetic replications: '+str(data['invalid_replications']),
               'REAL_OUTCOME_VALUES_READ=FALSE; REAL_R3_EXECUTED=FALSE; REAL_BOOTSTRAP_REPLICATIONS_EXECUTED=0.',
               'No result-specific branches. No real coefficient values or p-values copied. No real Holm.',
               'Future real R3 remains B=9999, seed=20260903, district-clustered, with the complete frozen physical-anomaly model.',
               'Any invalid draw means HOLD; no dropping, replacement, redraw or effective-B correction.',
               'R3/R4/R5/R6 execution is NOT_AUTHORIZED. Primary ER1 is not replaced.',
               'Two independent synthetic validation processes: '+reproduction['status']+'.',
               'Input identities and all three rendered output bytes must agree. No timestamps or local paths.','',
               '## Methodological references','',
               'The frozen full-design CR2 path is retained. General CR2 background: https://jepusto.com/posts/Pusto-Tipton-2018-Theorem-2-redux/',
               'Restricted wild-bootstrap background: https://journals.sagepub.com/doi/abs/10.1177/1536867X19830877',
               'These references do not replace or amend the frozen ED1 implementation.','',
               'NEXT_ACTION='+NEXT]
    payloads = {CSV:csv_bytes(rows),REPORT:('\n'.join(report)+'\n').encode('utf-8')}
    locked = dict(data,reproducibility=reproduction,artifact_sha256={p:sha(b) for p,b in payloads.items()})
    payloads[LOCK] = json_bytes(locked)
    return payloads


def write_exact(path,payload):
    payload.decode('utf-8')
    if b'\r' in payload or payload.startswith(b'\xef\xbb\xbf') or not payload.endswith(b'\n') or payload.endswith(b'\n\n'):
        raise ValueError('Canonical byte contract')
    if path.exists():
        if path.read_bytes()!=payload:
            raise RuntimeError('Existing candidate differs; no overwrite permitted')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(payload)


def build(destination):
    preflight()
    destination = destination.resolve()
    if destination != ROOT and ROOT in destination.parents:
        raise ValueError('Use repository root or external audit destination')
    with tempfile.TemporaryDirectory(prefix='er2-r3a-workers-') as temp:
        records = []
        for i in (1,2):
            path = Path(temp)/f'run{i}.json'
            subprocess.run([sys.executable,str(ROOT/SCRIPT),'--synthetic-worker',str(path)],cwd=ROOT,check=True)
            records.append(path.read_bytes())
        if records[0]!=records[1]:
            raise RuntimeError('ER2_R3A_FAIL_DETERMINISM')
        rep = {'status':'PASS','independent_processes':2,'run1_sha256':sha(records[0]),
               'run2_sha256':sha(records[1]),'synthetic_data_and_calculations_exact':True,'all_rendered_outputs_exact':True}
        one,two = (render(json.loads(r),rep) for r in records)
        if one!=two:
            raise RuntimeError('ER2_R3A_FAIL_DETERMINISM: rendering')
        for p,b in one.items():
            write_exact(destination/p,b)
    preflight()
    return {'verdict':json.loads(records[0])['final_verdict'],'artifact_sha256':{p:sha(b) for p,b in one.items()},'reproducibility':rep}


def main():
    parser = argparse.ArgumentParser(description='Synthetic-only named-coefficient WCR adapter validation')
    parser.add_argument('--output-root',type=Path,default=ROOT)
    parser.add_argument('--synthetic-worker',type=Path)
    args = parser.parse_args()
    if args.synthetic_worker:
        destination = args.synthetic_worker.resolve()
        if destination==ROOT or ROOT in destination.parents:
            raise ValueError('Synthetic worker output must be external')
        write_exact(destination,json_bytes(validate()))
    else:
        print(json_bytes(build(args.output_root)).decode('utf-8'),end='')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
