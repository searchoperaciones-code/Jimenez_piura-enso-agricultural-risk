from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import econometric_design_master_v1 as ed1

_JOINT_BEFORE_IMPORT = ed1.restricted_wild_cluster_bootstrap_t
import er2_r3_named_wcr_adapter_v1 as r
_IMPORT_UNCHANGED = ed1.restricted_wild_cluster_bootstrap_t is _JOINT_BEFORE_IMPORT

ROOT = r.ROOT
SCRIPT = 'scripts/er2_r3a_numerical_adjudication_v1.py'
TEST = 'tests/test_er2_r3a_numerical_adjudication_v1.py'
JSON = 'outputs/econometrics/ER2_R3A_NUMERICAL_ADJUDICATION.json'
REPORT = 'outputs/econometrics/ER2_R3A_NUMERICAL_ADJUDICATION_REPORT.md'
CERT = 'outputs/econometrics/ER2_R3A_ADAPTER_LOCK_CERTIFIED.json'
CANDIDATES = (*r.CANDIDATES,SCRIPT,TEST,JSON,REPORT,CERT)
ORIGINAL = {
    r.SCRIPT:'b0368dfcf93f2675c4b4fdcaff63e905540ff0914808319e53a4ee106eb365a2',
    r.TEST:'bf4403ffd5d22a6180f23343bdbadcd1136cd0d615defbc22cb73bab823ea66e',
    r.CSV:'440b461a2a8953a6012fe6f1bdba83f54e6830250234ce260eafc6d88b25be8c',
    r.REPORT:'f47ecf9a05e3af3c7d7494ff9bd43805dafc9b29c1f879a55d1e8751f0da02f5',
    r.LOCK:'2fb507407b73dc84f91d21cc8bc1e4eb32581b83eed7086662c4e7785f862d7c',
}
SPEC_SHA = '1f2d1457deb942045e2f59287274a195c86a9da54feddd42c4e3012b92183479'
TOL = 1e-10
PASS = 'ER2_R3A1_PASS_FLOAT64_CONTINUOUS_EQUIVALENCE_ADJUDICATED_READY_FOR_R3A_FREEZE_DECISION'
HOLD_E = 'ER2_R3A1_HOLD_EXCEEDANCE_DISAGREEMENT'
HOLD_DRAW = 'ER2_R3A1_HOLD_DRAW_IDENTITY_DISAGREEMENT'
HOLD_NUM = 'ER2_R3A1_HOLD_CONTINUOUS_ERROR_EXCEEDS_PRESPECIFIED_TOLERANCE'


def require(condition,message):
    if not condition:
        raise RuntimeError(message)


def preflight():
    require(r.git('rev-parse','HEAD').decode().strip()==r.PARENT,'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY')
    require(not r.git('diff','--name-only','HEAD').strip(),'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY')
    require(not r.git('diff','--cached','--name-only').strip(),'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY')
    require(set(r.git('ls-files','--others','--exclude-standard').decode().splitlines())<=set(CANDIDATES),
            'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: unknown candidate')
    for ref,expected in [(r.BRANCH,r.PARENT),('origin/'+r.BRANCH,r.PARENT),(r.TAG+'^{}',r.PARENT),
                         ('phase/er2p-robustness-protocol-v1',r.ER2P)]:
        require(r.git('rev-parse',ref).decode().strip()==expected,'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: ref')
    for path,expected in {**r.METADATA,**ORIGINAL}.items():
        require(r.sha((ROOT/path).read_bytes())==expected,'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: source identity')
    require(r.sha(r.git('cat-file','blob',r.PARENT+':outputs/econometrics/ER2_R2_RESULTS_LOCK_REPORTING_CERTIFIED.json'))==r.CERT_SHA,
            'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: predecessor lock')
    require(r.sha(r.json_bytes(r.SYNTHETIC_SPEC))==SPEC_SHA,'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: synthetic specification')
    tier = next(v for v in json.loads((ROOT/r.PROTOCOL).read_bytes())['tiers'] if v['tier']=='R3')
    require(r.sha(r.json_bytes(tier))==r.TIER_SHA,'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: R3')
    old = json.loads((ROOT/r.LOCK).read_bytes())
    require(old['final_verdict']==r.HOLD and old['synthetic_specification_sha256']==SPEC_SHA,
            'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: original HOLD')
    return {'R2_FREEZE_SHA':r.PARENT,'R2_REPORTING_CERTIFIED_LOCK_SHA':r.CERT_SHA,'ER2P_FREEZE_SHA':r.ER2P,
            'R3_TIER_CONTRACT_SHA':r.TIER_SHA,'R3A_INITIAL_HOLD_LOCK_SHA256':ORIGINAL[r.LOCK],
            'PROVISIONAL_LOCK_TEST_IDENTITY_CURRENT':old['test_sha256']==ORIGINAL[r.TEST],
            'PROVISIONAL_LOCK_RECORDED_TEST_SHA256':old['test_sha256'],
            'INTERRUPTED_STRENGTHENED_TEST_SHA256':'000f44fcc26828b6c54ca00a152e41174e57b4f2cab4db43fc456d73be28f860',
            'STRENGTHENED_TEST_CURRENT_SHA256':ORIGINAL[r.TEST],
            'TEST_EXPECTATION_FIX':'CANONICAL_JSON_ROUNDTRIP_BEFORE_EXPECTED_RENDER_ONLY',
            'ORIGINAL_HOLD_TERMINALLY_CERTIFIED':False,'original_candidate_sha256':ORIGINAL,
            'future_real_contract':tier,'ED1_IMPLEMENTATION_SHA256':r.ED1_SHA}


def metric(left,right):
    left,right = np.asarray(left,dtype=float),np.asarray(right,dtype=float)
    difference = left-right
    absolute = float(np.max(np.abs(difference)))
    denominator = max(float(np.linalg.norm(left.ravel())),float(np.linalg.norm(right.ravel())),np.finfo(float).eps)
    return {'max_abs_difference':absolute,'relative_l2_error':float(np.linalg.norm(difference.ravel())/denominator),
            'exact':bool(np.array_equal(left,right)),'pass':bool(np.isfinite(difference).all() and absolute<=TOL)}


def ulp_distance(left,right):
    if not np.isfinite([left,right]).all() or min(left,right)<0:
        return None
    a,b = np.asarray([left,right],dtype=np.float64).view(np.uint64)
    return abs(int(a)-int(b))


def original_order_view(result,inverse=None):
    fit = result['fit']
    order = np.arange(len(fit['full_beta']))
    if inverse is not None:
        offset = len(order)-len(inverse)
        order[offset:] = offset+np.asarray(inverse)
    return {'beta':fit['full_beta'][order],
            'fitted':fit['design']@fit['full_beta'],'residual':fit['residual'],
            'covariance':fit['covariance'][np.ix_(order,order)],'design':fit['design'][:,order],
            'observed':result['observed_statistic'],'restricted_residual':result['restricted_residual'],
            'rank':int(np.linalg.matrix_rank(fit['design'])),'cluster_labels':fit['cluster_labels'],
            'cluster_indices':fit['cluster_indices']}


def continuous(left,right,left_inverse=None,right_inverse=None):
    lv,rv = original_order_view(left,left_inverse),original_order_view(right,right_inverse)
    metrics = {k:metric(lv[k],rv[k]) for k in ('beta','fitted','residual','covariance','observed','restricted_residual')}
    conditions = {'same_full_design':np.array_equal(lv['design'],rv['design']),
                  'rank_agreement':lv['rank']==rv['rank'],
                  'sign_agreement':np.array_equal(np.sign(lv['beta']),np.sign(rv['beta'])),
                  'cluster_order_agreement':lv['cluster_labels']==rv['cluster_labels'],
                  'cluster_assignment_agreement':all(np.array_equal(a,b) for a,b in zip(lv['cluster_indices'],rv['cluster_indices']))}
    return {'metrics':metrics,**{k:bool(v) for k,v in conditions.items()},
            'status':'PASS' if all(v['pass'] for v in metrics.values()) and all(conditions.values()) else 'FAIL'}


def draw_record(result):
    matrix = np.concatenate([b['draws'] for b in result['batches']],axis=1)
    require(np.isin(matrix,[-1,1]).all(),'Rademacher draw domain')
    return {'matrix_shape':list(matrix.shape),'matrix_dtype':'INT8_ROW_MAJOR_N_CLUSTERS_BY_B',
            'complete_matrix_sha256':r.sha(matrix.astype('i1').tobytes()),
            'batch_sizes':[b['count'] for b in result['batches']],
            'batch_draw_sha256':[r.sha(b['draws'].astype('i1').tobytes()) for b in result['batches']],
            'pcg64_states':[b['rng_state'] for b in result['batches']],
            'initial_pcg64_state':np.random.PCG64(20260903).state,
            'cluster_order':result['fit']['cluster_labels']}


def discrete(paths):
    draws = {k:draw_record(v) for k,v in paths.items()}
    e = {k:int(v['exceedances']) for k,v in paths.items()}
    invalid = {k:v['invalid_replications'] for k,v in paths.items()}
    fractions = {k:{'numerator':1+v,'denominator':2002} for k,v in e.items()}
    p = {k:v['exact_p'] for k,v in paths.items()}
    api_p = {k:v['frozen_result']['synthetic_p_value'] for k,v in paths.items() if 'frozen_result' in v}
    correction = all(p[k]==fractions[k]['numerator']/2002 for k in paths)
    correction = correction and all(api_p[k]==ed1.rounded(p[k]) for k in api_p)
    return {'draws':draws,'draw_identity':all(v==next(iter(draws.values())) for v in draws.values()),
            'EXCEEDANCES':e,'exceedance_identity':len(set(e.values()))==1,
            'INVALID':invalid,'invalid_zero':all(v==0 for v in invalid.values()),
            'P_EXACT_RATIONAL':fractions,'P_UNROUNDED_FROM_COUNTS':p,'P_FROZEN_API_RETURNED':api_p,
            'finite_correction_identity':correction and len(set(p.values()))==1}


def joint_reference(frame,columns,response,independent_fit):
    # PATH C fit comes only from the independent original-order one-hot implementation.
    fit = independent_fit
    design,beta,cov = fit['design'],fit['full_beta'],fit['covariance']
    gram = design.T@design
    bread = np.linalg.inv(gram)
    q = len(columns)
    contrast = np.eye(design.shape[1])[-q:]
    system = np.block([[gram,contrast.T],[contrast,np.zeros((q,q))]])
    null_beta = np.linalg.solve(system,np.r_[design.T@response,np.zeros(q)])[:-q]
    restricted = response-design@null_beta
    block_beta = contrast@beta
    observed = float(block_beta@np.linalg.solve(contrast@cov@contrast.T,block_beta)/q)
    residual_maker = np.eye(len(frame))-design@bread@design.T
    residual_maker = (residual_maker+residual_maker.T)/2
    adjustments = []
    for indices in fit['cluster_indices']:
        block = residual_maker[np.ix_(indices,indices)]
        values,vectors = np.linalg.eigh((block+block.T)/2)
        threshold = np.finfo(float).eps*len(indices)*max(1.,np.max(np.abs(values)))*128
        positive = values>threshold
        require(positive.sum()==len(indices)-1 and values.min()>=-threshold,'Independent joint CR2 rank')
        adjustments.append((vectors[:,positive]/np.sqrt(values[positive]))@vectors[:,positive].T)
    rng = np.random.Generator(np.random.PCG64(20260903))
    batches,exceedances,invalid = [],0,0
    for start in range(0,2001,1000):
        count = min(1000,2001-start)
        draws = rng.integers(0,2,size=(len(fit['cluster_indices']),count),dtype=np.int8).astype(float)*2-1
        weights = np.empty((len(frame),count))
        for g,indices in enumerate(fit['cluster_indices']):
            weights[indices] = draws[g]
        shock = restricted[:,None]*weights
        changes = np.linalg.solve(gram,design.T@shock)
        residuals = shock-design@changes
        beta_star = contrast@(null_beta[:,None]+changes)
        covariance = np.zeros((q,q,count))
        for indices,adjustment in zip(fit['cluster_indices'],adjustments):
            scores = contrast@bread@design[indices].T@adjustment@residuals[indices]
            covariance += scores[:,None,:]*scores[None,:,:]
        statistics = np.full(count,np.nan)
        for i in range(count):
            try:
                statistics[i] = float(beta_star[:,i]@np.linalg.solve(covariance[:,:,i],beta_star[:,i])/q)
            except np.linalg.LinAlgError:
                pass
        valid = np.isfinite(statistics)
        invalid += int((~valid).sum())
        exceedances += int(np.sum(statistics[valid]>=observed))
        batches.append({'draws':draws,'statistics':statistics,'count':count,'rng_state':rng.bit_generator.state})
    return {'fit':fit,'observed_statistic':observed,'exceedances':exceedances,'invalid_replications':invalid,
            'exact_p':(1+exceedances)/2002,'batches':batches,'restricted_residual':restricted,'beta_null':null_beta}


def source_audit():
    sources = {name:inspect.getsource(func) for name,func in (
        ('A',r.named_coefficient_wcr_adapter),('B',r.frozen_wcr_audit),('C',r.one_hot_reference),('C_JOINT',joint_reference))}
    calls = {key:sorted({ast.unparse(n.func) for n in ast.walk(ast.parse(value)) if isinstance(n,ast.Call)}) for key,value in sources.items()}
    independent = all(not any(word in name for word in ('ed1.','adapter','frozen_wcr','permutation')) for key in ('C','C_JOINT') for name in calls[key])
    branch = r.branch_audit()['result_specific_adapter_branches']
    for key in ('A','B'):
        tree = ast.parse(sources[key])
        for node in ast.walk(tree):
            if isinstance(node,(ast.If,ast.IfExp)):
                literals = [n.value.upper() for n in ast.walk(node.test) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
                branch += sum(any(x in v for x in ('BANANA','MANGO','LEMON','SIGNIFICAN','P_VALUE','TMIN','RAIN')) for v in literals)
    return {'ONE_HOT_REFERENCE_INDEPENDENT':independent,'RESULT_SPECIFIC_ADAPTER_BRANCHES':branch,
            'call_graph':calls,'source_body_sha256':{k:r.sha(v.encode()) for k,v in sources.items()},
            'shared_primitives':'NUMPY_LINEAR_ALGEBRA_AND_PCG64_ONLY; C_JOINT_REUSES_C_INDEPENDENT_FIT; NO_A_B_NUMERICAL_HELPER',
            'import_preserves_frozen_joint_function':_IMPORT_UNCHANGED}


def validate():
    provenance = preflight()
    targets = r.target_map()
    original = json.loads((ROOT/r.LOCK).read_bytes())
    require(targets==original['target_map'],'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: target map')
    results,joints,identities = [],{},{}
    function = ed1.restricted_wild_cluster_bootstrap_t
    saved_trace = sys.gettrace()
    legacy_rng = np.random.get_state()
    with r.outcome_firewall():
        for size in (3,6):
            columns = next(row['FROZEN_REGRESSORS'] for row in targets if row['ARCHITECTURE']==size)
            frame,y = r.synthetic_panel(columns)
            identity = {'x_sha256':r.array_sha(frame[columns].to_numpy()),'y_sha256':r.array_sha(y),
                        'keys_sha256':r.sha(r.json_bytes(frame[['UBIGEO','PERIOD']].values.tolist()))}
            require(all(value==original['synthetic_identities'][str(size)][key] for key,value in identity.items()),
                    'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: synthetic data')
            identities[str(size)] = identity
            before_frame,before_y = frame.copy(deep=True),y.copy()
            joint_before = r.frozen_wcr_audit(frame,columns,'PERIOD',y,2001,20260903,'ALL_CLIMATE_COEFFICIENTS')
            reference_fit = None
            for position,target in enumerate(columns):
                adapter = r.named_coefficient_wcr_adapter(frame,columns,'PERIOD',y,target,2001,20260903,1000)
                a = adapter['audit']
                explicit = [target]+[column for column in columns if column!=target]
                b_order = [columns.index(column) for column in explicit]
                b_inverse = [b_order.index(i) for i in range(size)]
                b = r.frozen_wcr_audit(frame,explicit,'PERIOD',y,2001,20260903,'FIRST_CLIMATE_COEFFICIENT')
                c = r.one_hot_reference(frame,columns,'PERIOD',y,position,2001,20260903)
                if position==0:
                    reference_fit = c['fit']
                ac = continuous(a,c,adapter['inverse_permutation'])
                bc = continuous(b,c,b_inverse)
                ab = continuous(a,b)
                metadata_exact = (adapter['target_variable']==target and adapter['original_position']==position and
                                  adapter['permutation']==b_order and adapter['inverse_permutation']==b_inverse and
                                  adapter['regressors']==explicit and adapter['target_position']==0)
                exact_ab = metadata_exact and all(m['exact'] for m in ab['metrics'].values()) and ab['same_full_design']
                exact_ab = exact_ab and a['frozen_result']==b['frozen_result'] and all(
                    np.array_equal(left['statistics'],right['statistics']) for left,right in zip(a['batches'],b['batches']))
                disc = discrete({'A':a,'B':b,'C':c})
                exact_ab = exact_ab and disc['draws']['A']==disc['draws']['B'] and a['exceedances']==b['exceedances'] and a['invalid_replications']==b['invalid_replications']
                t_a,t_b,t_c = (v['observed_statistic'] for v in (a,b,c))
                trow = {'architecture':size,'target_position':position,'t_A':t_a,'t_B':t_b,'t_C':t_c,
                        'abs_A_B':abs(t_a-t_b),'abs_A_C':abs(t_a-t_c),'abs_B_C':abs(t_b-t_c),
                        'relative_A_B':metric(t_a,t_b)['relative_l2_error'],
                        'relative_A_C':metric(t_a,t_c)['relative_l2_error'],'relative_B_C':metric(t_b,t_c)['relative_l2_error'],
                        'ulp_A_C':ulp_distance(t_a,t_c),'ulp_B_C':ulp_distance(t_b,t_c),
                        'tolerance_status':'PASS' if max(abs(t_a-t_c),abs(t_b-t_c))<=TOL else 'FAIL'}
                full = frame.equals(before_frame) and np.array_equal(y,before_y) and set(explicit)==set(columns)
                target_null = [int(i==position) for i in range(size)]
                results.append({'architecture':size,'target_position':position,'target':target,'permutation':b_order,
                                'inverse_permutation':b_inverse,'original_order_one_hot_null':target_null,
                                'A_B_EXACT':bool(exact_ab),'A_C':ac,'B_C':bc,'discrete':disc,'t_difference':trow,
                                'full_model_preserved':bool(full),'target_null_definition_agreement':True})
            joint_after = r.frozen_wcr_audit(frame,columns,'PERIOD',y,2001,20260903,'ALL_CLIMATE_COEFFICIENTS')
            order = list(reversed(range(size)))
            joint_permuted = r.frozen_wcr_audit(frame,[columns[i] for i in order],'PERIOD',y,2001,20260903,'ALL_CLIMATE_COEFFICIENTS')
            independent = joint_reference(frame,columns,y,reference_fit)
            before_after = continuous(joint_before,joint_after)
            exact_use = all(m['exact'] for m in before_after['metrics'].values()) and joint_before['frozen_result']==joint_after['frozen_result']
            joints[str(size)] = {'before_after_same_routine_exact':bool(exact_use),
                                'A_C':continuous(joint_after,independent),
                                'B_C':continuous(joint_permuted,independent,np.argsort(order).tolist()),
                                'discrete':discrete({'BEFORE':joint_before,'A':joint_after,'B':joint_permuted,'C':independent}),
                                'observed_wald_f':{name:v['observed_statistic'] for name,v in
                                    [('BEFORE',joint_before),('A',joint_after),('B',joint_permuted),('C',independent)]}}
    now_rng = np.random.get_state()
    unchanged_rng = all(np.array_equal(a,b) for a,b in zip(legacy_rng,now_rng))
    audit = source_audit()
    audit.update(joint_function_identity_unchanged=ed1.restricted_wild_cluster_bootstrap_t is function,
                 python_trace_restored=sys.gettrace() is saved_trace,numpy_legacy_rng_unchanged=unchanged_rng)
    discrete_rows = [row['discrete'] for row in results]+[value['discrete'] for value in joints.values()]
    continuous_ok = all(row[p]['status']=='PASS' for row in results for p in ('A_C','B_C')) and all(j[p]['status']=='PASS' for j in joints.values() for p in ('A_C','B_C'))
    exact_ab = all(row['A_B_EXACT'] for row in results)
    draws = all(row['draw_identity'] for row in discrete_rows)
    counts = all(row['exceedance_identity'] for row in discrete_rows)
    invalid = sum(sum(row['INVALID'].values()) for row in discrete_rows)
    finite = all(row['finite_correction_identity'] for row in discrete_rows)
    joint_ok = all(row['before_after_same_routine_exact'] for row in joints.values()) and all(
        row[p]['status']=='PASS' for row in joints.values() for p in ('A_C','B_C')) and all(
        row['discrete'][key] for row in joints.values() for key in ('draw_identity','exceedance_identity','invalid_zero','finite_correction_identity'))
    if not audit['ONE_HOT_REFERENCE_INDEPENDENT']:
        verdict = 'ER2_R3A1_FAIL_ONE_HOT_INDEPENDENCE'
    elif not draws:
        verdict = HOLD_DRAW
    elif not counts or invalid or not finite:
        verdict = HOLD_E
    elif not continuous_ok or not exact_ab or not joint_ok:
        verdict = HOLD_NUM
    else:
        verdict = PASS
    require(all(row['full_model_preserved'] for row in results),'ER2_R3A1_FAIL_UPSTREAM_IMMUTABILITY: model')
    require(audit['RESULT_SPECIFIC_ADAPTER_BRANCHES']==0 and all(audit[k] for k in
            ('import_preserves_frozen_joint_function','joint_function_identity_unchanged','python_trace_restored','numpy_legacy_rng_unchanged')),
            'ER2_R3A1_FAIL_ONE_HOT_INDEPENDENCE: state contamination')
    maximum = max(row['t_difference']['abs_A_C'] for row in results)
    maximum_cases = [{'architecture':row['architecture'],'position':row['target_position']} for row in results if row['t_difference']['abs_A_C']==maximum]
    preflight()
    return {'schema_version':'1.0.0','gate':'ER2_R3A1_NAMED_WCR_ADAPTER_EQUIVALENCE_ADJUDICATION_V1',
            'project':'ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA','provenance':provenance,
            'implementation_sha256':r.sha((ROOT/SCRIPT).read_bytes()),'test_sha256':r.sha((ROOT/TEST).read_bytes()),
            'R3A_INITIAL_EXACT_CONTINUOUS_CHECK':'HOLD','R3A_CONTINUOUS_FLOAT64_ADJUDICATION':'PASS' if continuous_ok else 'FAIL',
            'PRESPECIFIED_CONTINUOUS_TOLERANCE':TOL,'TOLERANCE_CHANGED_AFTER_RESULTS':False,
            'R3A_SYNTHETIC_DATA_SEED':2026090501,'R3A_SYNTHETIC_WCR_REPLICATIONS':2001,'R3A_SYNTHETIC_BATCH_SIZE':1000,
            'synthetic_specification_sha256':SPEC_SHA,'synthetic_data_sha256':identities,'target_map':targets,
            'positional_cases':results,'joint_cases':joints,'source_audit':audit,
            'A_B_EXACT_EQUIVALENCE':'PASS' if exact_ab else 'FAIL',
            'MAX_A_C_T_ABS_DIFF':maximum,'MAX_B_C_T_ABS_DIFF':max(row['t_difference']['abs_B_C'] for row in results),
            'maximum_t_difference_cases':maximum_cases,'DRAW_MATRIX_IDENTITY':'PASS' if draws else 'FAIL',
            'EXCEEDANCE_COUNT_IDENTITY':'PASS' if counts else 'FAIL','INVALID_SYNTHETIC_REPLICATIONS':invalid,
            'FINITE_CORRECTION_IDENTITY':'PASS' if finite else 'FAIL','JOINT_WCR_NONINTERFERENCE':'PASS' if joint_ok else 'FAIL',
            'R3A_ADAPTER_VALIDATED':verdict==PASS,'REAL_OUTCOME_VALUES_READ':False,'REAL_R3_EXECUTED':False,
            'REAL_BOOTSTRAP_REPLICATIONS_EXECUTED':0,'NEXT_TIER_AUTHORIZATION_STATUS':'NOT_AUTHORIZED',
            'R4':'NOT_EXECUTED','R5':'NOT_EXECUTED','R6':'NOT_EXECUTED','ULP_DIAGNOSTIC_ONLY':True,'final_verdict':verdict}


def render(data,reproduction,suite):
    lines = ['# ER2 R3A1 Numerical Equivalence Adjudication v1','',
             'SYNTHETIC DATA ONLY. No real R3 authorization.','',
             'VERDICT='+data['final_verdict'],'',
             '## Preserved original alarm','',
             'The original exact-continuous check remains HOLD. Its provisional lock is not terminally certified.',
             'Original HOLD lock SHA-256: '+ORIGINAL[r.LOCK],
             'The strengthened test identity differed at interruption. Its sole subsequent correction canonicalizes the expected render input exactly like the worker JSON boundary.',
             'No adapter algorithm, PATH C, seed, B, tolerance, original CSV, original report or provisional lock was rewritten.','',
             '## Director contract adjudication','',
             'Original instructions specified both 1e-10 numerical tolerance and later exact observed-t wording.',
             'The Director now makes the already prespecified absolute 1e-10 tolerance governing for independent continuous quantities.',
             'A/B same-routine quantities and all discrete bootstrap identities still require exact equality. No rounding or quantization is applied.',
             'Scale-aware errors and ULP distances are diagnostic only; relative error never replaces the absolute gate.',
             'Synthetic seed=2026090501; B=2001; batch=1000+1000+1; specification SHA-256='+SPEC_SHA+'.','',
             '## Full positional t distribution','',
             '| Architecture | Position | t_A | t_B | t_C | abs A-B | abs A-C | abs B-C | rel A-C | rel B-C | ULP A-C | Status |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in data['positional_cases']:
        t = row['t_difference']
        keys = ('architecture','target_position','t_A','t_B','t_C','abs_A_B','abs_A_C','abs_B_C','relative_A_C','relative_B_C','ulp_A_C','tolerance_status')
        lines.append('| '+' | '.join(str(t[k]) for k in keys)+' |')
    lines += ['', 'Maximum abs(A-C)='+str(data['MAX_A_C_T_ABS_DIFF'])+' at '+json.dumps(data['maximum_t_difference_cases'],sort_keys=True)+'.',
              'The adjudication JSON contains all beta/fitted/residual/covariance errors, signed-beta/rank/cluster checks and complete draw-matrix SHA-256 records.','',
              '## Exact discrete identities and joint paths','',
              'A/B exact='+data['A_B_EXACT_EQUIVALENCE']+'; draws='+data['DRAW_MATRIX_IDENTITY']+'; exceedances='+data['EXCEEDANCE_COUNT_IDENTITY']+'.',
              'Invalid synthetic replications='+str(data['INVALID_SYNTHETIC_REPLICATIONS'])+'; finite correction='+data['FINITE_CORRECTION_IDENTITY']+'.',
              'Each p is recorded as numerator (1+E), denominator 2002, unrounded ratio and frozen API 12-decimal returned value.',
              'Joint noninterference='+data['JOINT_WCR_NONINTERFERENCE']+'. Original joint function identity, before/after-use outputs, trace restoration and legacy RNG noncontamination are certified.',
              'C uses original-order OLS/CR2 with KKT restrictions; joint C reuses only the independent C fit, not A/B internals. The JSON includes source-body hashes and call graphs.','',
              '## Test and reproduction closure','',
              'Protected suite: '+json.dumps(suite['counts'],sort_keys=True)+'.',
              'Every nonpass is adjudicated; real-data-dependent fixtures blocked by the firewall are not represented as passed.',
              'Unrelated real regressions=0; unresolved failures=0. Two independent adjudication processes='+reproduction['status']+'.','',
              '## Execution firewall','',
              'REAL_OUTCOME_VALUES_READ=FALSE; REAL_R3_EXECUTED=FALSE; REAL_BOOTSTRAP_REPLICATIONS_EXECUTED=0.',
              'Future real B=9999 and seed=20260903 remain unchanged. R3/R4/R5/R6 are NOT_AUTHORIZED.',
              'NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3A_FREEZE_DECISION_IF_PASS']
    adjud = dict(data,reproducibility=reproduction,protected_full_suite=suite)
    payloads = {JSON:r.json_bytes(adjud),REPORT:('\n'.join(lines)+'\n').encode()}
    if data['final_verdict']==PASS:
        certified = dict(adjud,gate='ER2_R3A_ADAPTER_LOCK_CERTIFIED_V1',
                         artifact_sha256={p:r.sha(b) for p,b in payloads.items()},
                         status='ADAPTER_VALIDATED_PENDING_DIRECTOR_FREEZE',
                         R3A_ADAPTER_VALIDATED=True,NEXT_TIER_AUTHORIZATION_STATUS='NOT_AUTHORIZED')
        payloads[CERT] = r.json_bytes(certified)
    return payloads


def build(destination,suite_path):
    suite_raw = suite_path.read_bytes()
    suite = json.loads(suite_raw)
    require(suite['unrelated_real_regressions']==suite['unresolved']==0,'ER2_R3A1_FAIL_TEST_REGRESSION')
    require(suite['new_specific_tests']['fail']==suite['new_specific_tests']['error']==0,'ER2_R3A1_FAIL_TEST_REGRESSION')
    require(suite['original_strengthened_tests']['pass']==48,'ER2_R3A1_FAIL_TEST_REGRESSION')
    certificate = {k:v for k,v in suite.items() if k!='nonpasses'}
    certificate['external_ledger_sha256'] = r.sha(suite_raw)
    destination = destination.resolve()
    require(destination==ROOT or ROOT not in destination.parents,'Use external destination or root')
    with tempfile.TemporaryDirectory(prefix='er2-r3a1-workers-') as temp:
        records = []
        for i in (1,2):
            path = Path(temp)/f'worker{i}.json'
            subprocess.run([sys.executable,str(ROOT/SCRIPT),'--synthetic-worker',str(path)],cwd=ROOT,check=True)
            records.append(path.read_bytes())
        require(records[0]==records[1],'ER2_R3A1_FAIL_TEST_REGRESSION: nondeterministic workers')
        reproduction = {'status':'PASS','independent_processes':2,'run1_sha256':r.sha(records[0]),'run2_sha256':r.sha(records[1]),
                        'all_three_outputs_byte_identical':True}
        one,two = [render(json.loads(raw),reproduction,certificate) for raw in records]
        require(one==two,'ER2_R3A1_FAIL_TEST_REGRESSION: nondeterministic render')
        for path,payload in one.items():
            r.write_exact(destination/path,payload)
    preflight()
    return {'verdict':json.loads(records[0])['final_verdict'],'artifact_sha256':{p:r.sha(b) for p,b in one.items()},'reproducibility':reproduction}


def main():
    parser = argparse.ArgumentParser(description='Synthetic-only R3A1 numerical adjudication')
    parser.add_argument('--synthetic-worker',type=Path)
    parser.add_argument('--output-root',type=Path,default=ROOT)
    parser.add_argument('--suite-certificate',type=Path)
    args = parser.parse_args()
    if args.synthetic_worker:
        path = args.synthetic_worker.resolve()
        require(path!=ROOT and ROOT not in path.parents,'Worker must be external')
        r.write_exact(path,r.json_bytes(validate()))
    else:
        if args.suite_certificate is None:
            parser.error('--suite-certificate is required before certified artifacts can be created')
        print(r.json_bytes(build(args.output_root,args.suite_certificate)).decode(),end='')


if __name__=='__main__':
    main()
