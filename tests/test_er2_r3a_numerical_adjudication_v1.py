from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import er2_r3a_numerical_adjudication_v1 as a
from er2_r3a_numerical_adjudication_v1 import r


class R3A1AdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = a.validate()

    def test_01_exact_r2_and_r3_provenance(self):
        p = self.data['provenance']
        self.assertEqual(p['R2_FREEZE_SHA'],r.PARENT)
        self.assertEqual(p['R2_REPORTING_CERTIFIED_LOCK_SHA'],r.CERT_SHA)
        self.assertEqual(p['R3_TIER_CONTRACT_SHA'],r.TIER_SHA)

    def test_02_original_hold_bytes_preserved(self):
        for path in (r.SCRIPT,r.CSV,r.REPORT,r.LOCK):
            self.assertEqual(r.sha((r.ROOT/path).read_bytes()),a.ORIGINAL[path])
        self.assertEqual(self.data['R3A_INITIAL_EXACT_CONTINUOUS_CHECK'],'HOLD')

    def test_03_interrupted_test_identity_not_concealed(self):
        p = self.data['provenance']
        self.assertIs(p['PROVISIONAL_LOCK_TEST_IDENTITY_CURRENT'],False)
        self.assertIs(p['ORIGINAL_HOLD_TERMINALLY_CERTIFIED'],False)
        self.assertNotEqual(p['PROVISIONAL_LOCK_RECORDED_TEST_SHA256'],p['STRENGTHENED_TEST_CURRENT_SHA256'])
        self.assertEqual(p['TEST_EXPECTATION_FIX'],'CANONICAL_JSON_ROUNDTRIP_BEFORE_EXPECTED_RENDER_ONLY')

    def test_04_original_strict_test_still_present(self):
        source = (r.ROOT/r.TEST).read_text(encoding='utf-8')
        self.assertIn('test_38_exact_gate_cannot_be_replaced_by_tolerance',source)
        self.assertIn("self.assertEqual(v['verdict'],r.HOLD)",source)

    def test_05_prespecified_seed_and_tolerance(self):
        self.assertEqual(self.data['R3A_SYNTHETIC_DATA_SEED'],2026090501)
        self.assertEqual(self.data['synthetic_specification_sha256'],a.SPEC_SHA)
        self.assertEqual(self.data['PRESPECIFIED_CONTINUOUS_TOLERANCE'],1e-10)
        self.assertIs(self.data['TOLERANCE_CHANGED_AFTER_RESULTS'],False)

    def test_06_b_and_batch_unchanged(self):
        self.assertEqual(self.data['R3A_SYNTHETIC_WCR_REPLICATIONS'],2001)
        self.assertEqual(self.data['R3A_SYNTHETIC_BATCH_SIZE'],1000)
        self.assertEqual(self.data['provenance']['future_real_contract']['replications'],9999)
        self.assertEqual(self.data['provenance']['future_real_contract']['seed'],20260903)

    def test_07_nine_positional_cases(self):
        self.assertEqual({(v['architecture'],v['target_position']) for v in self.data['positional_cases']},
                         {(n,i) for n in (3,6) for i in range(n)})

    def test_08_ab_exact_all_quantities(self):
        self.assertEqual(self.data['A_B_EXACT_EQUIVALENCE'],'PASS')
        self.assertTrue(all(v['A_B_EXACT'] for v in self.data['positional_cases']))

    def test_09_ac_absolute_tolerance_all_quantities(self):
        for row in self.data['positional_cases']:
            self.assertEqual(row['A_C']['status'],'PASS')
            for value in row['A_C']['metrics'].values():
                self.assertLessEqual(value['max_abs_difference'],1e-10)

    def test_10_bc_absolute_tolerance_all_quantities(self):
        for row in self.data['positional_cases']:
            self.assertEqual(row['B_C']['status'],'PASS')
            for value in row['B_C']['metrics'].values():
                self.assertLessEqual(value['max_abs_difference'],1e-10)

    def test_11_near_zero_and_large_scale_do_not_bypass_absolute_gate(self):
        self.assertFalse(a.metric(0.,2e-10)['pass'])
        self.assertFalse(a.metric(1e6,1e6+1e-6)['pass'])
        self.assertTrue(a.metric(0.,5e-11)['pass'])

    def test_12_full_t_distribution_and_maximum(self):
        rows = [v['t_difference'] for v in self.data['positional_cases']]
        self.assertEqual(len(rows),9)
        for row in rows:
            self.assertEqual(row['abs_A_B'],abs(row['t_A']-row['t_B']))
            self.assertEqual(row['abs_A_C'],abs(row['t_A']-row['t_C']))
            self.assertEqual(row['abs_B_C'],abs(row['t_B']-row['t_C']))
            self.assertIn('relative_A_C',row)
            self.assertIn('relative_B_C',row)
        maximum = max(row['abs_A_C'] for row in rows)
        self.assertEqual(self.data['MAX_A_C_T_ABS_DIFF'],maximum)
        self.assertEqual(self.data['maximum_t_difference_cases'],[
            {'architecture':row['architecture'],'position':row['target_position']} for row in rows if row['abs_A_C']==maximum])

    def test_13_ulp_is_diagnostic_only(self):
        self.assertIs(self.data['ULP_DIAGNOSTIC_ONLY'],True)
        self.assertEqual(a.ulp_distance(1.,np.nextafter(1.,2.)),1)

    def test_14_complete_draw_hashes_and_order_exact(self):
        for row in self.data['positional_cases']:
            draws = row['discrete']['draws']
            self.assertEqual(draws['A'],draws['B'])
            self.assertEqual(draws['A'],draws['C'])
            self.assertEqual(draws['A']['matrix_shape'],[16,2001])
            self.assertEqual(draws['A']['batch_sizes'],[1000,1000,1])
            self.assertEqual(len(draws['A']['complete_matrix_sha256']),64)

    def test_15_integer_exceedances_exact(self):
        for row in self.data['positional_cases']:
            e = row['discrete']['EXCEEDANCES']
            self.assertEqual(e['A'],e['B'])
            self.assertEqual(e['A'],e['C'])
            self.assertTrue(all(type(value) is int for value in e.values()))

    def test_16_no_invalid_draws(self):
        self.assertEqual(self.data['INVALID_SYNTHETIC_REPLICATIONS'],0)
        self.assertTrue(all(row['discrete']['invalid_zero'] for row in self.data['positional_cases']))

    def test_17_pathological_invalid_still_hold(self):
        self.assertEqual(r.tier_status(1),'HOLD')
        self.assertEqual(r.tier_status(2001),'HOLD')
        self.assertEqual(r.tier_status(0),'COMPLETE')

    def test_18_rational_and_frozen_returned_p(self):
        for row in self.data['positional_cases']:
            d = row['discrete']
            for key in ('A','B','C'):
                fraction = d['P_EXACT_RATIONAL'][key]
                self.assertEqual(fraction,{'numerator':1+d['EXCEEDANCES'][key],'denominator':2002})
                self.assertEqual(d['P_UNROUNDED_FROM_COUNTS'][key],fraction['numerator']/fraction['denominator'])
            for key in ('A','B'):
                self.assertEqual(d['P_FROZEN_API_RETURNED'][key],round(d['P_UNROUNDED_FROM_COUNTS'][key],12))

    def test_19_correction_edges(self):
        self.assertEqual(r.finite_p(0,2001),1/2002)
        self.assertEqual(r.finite_p(2001,2001),1.)

    def test_20_independent_one_hot_call_graph(self):
        graph = self.data['source_audit']['call_graph']
        self.assertTrue(self.data['source_audit']['ONE_HOT_REFERENCE_INDEPENDENT'])
        for key in ('C','C_JOINT'):
            self.assertFalse(any('adapter' in name or 'ed1.' in name or 'frozen_wcr' in name for name in graph[key]))

    def test_21_sign_rank_null_and_cluster_agreement(self):
        for row in self.data['positional_cases']:
            self.assertEqual(sum(row['original_order_one_hot_null']),1)
            self.assertEqual(row['original_order_one_hot_null'][row['target_position']],1)
            self.assertIs(row['target_null_definition_agreement'],True)
            for path in ('A_C','B_C'):
                for key in ('same_full_design','rank_agreement','sign_agreement','cluster_order_agreement','cluster_assignment_agreement'):
                    self.assertTrue(row[path][key])

    def test_22_full_model_rows_response_unchanged(self):
        self.assertTrue(all(row['full_model_preserved'] for row in self.data['positional_cases']))

    def test_23_exact_21_name_map(self):
        rows = self.data['target_map']
        self.assertEqual(len(rows),21)
        self.assertEqual(len({(v['CROP_CODE'],v['VARIABLE']) for v in rows}),21)
        self.assertEqual(rows,r.target_map())

    def test_24_joint_before_after_and_independent_continuous(self):
        self.assertEqual(self.data['JOINT_WCR_NONINTERFERENCE'],'PASS')
        for row in self.data['joint_cases'].values():
            self.assertTrue(row['before_after_same_routine_exact'])
            self.assertEqual(row['A_C']['status'],'PASS')
            self.assertEqual(row['B_C']['status'],'PASS')
            self.assertTrue(row['discrete']['draw_identity'])
            self.assertTrue(row['discrete']['exceedance_identity'])
            self.assertTrue(row['discrete']['finite_correction_identity'])

    def test_25_no_global_state_contamination(self):
        for key in ('import_preserves_frozen_joint_function','joint_function_identity_unchanged','python_trace_restored','numpy_legacy_rng_unchanged'):
            self.assertTrue(self.data['source_audit'][key])

    def test_26_no_result_specific_branch(self):
        self.assertEqual(self.data['source_audit']['RESULT_SPECIFIC_ADAPTER_BRANCHES'],0)

    def test_27_real_outcome_firewall(self):
        with r.outcome_firewall(),self.assertRaises(r.RealOutcomeFirewall):
            (r.ROOT/'data/processed/panel_master.csv').read_bytes()
        self.assertIs(self.data['REAL_OUTCOME_VALUES_READ'],False)
        self.assertIs(self.data['REAL_R3_EXECUTED'],False)
        self.assertEqual(self.data['REAL_BOOTSTRAP_REPLICATIONS_EXECUTED'],0)

    def test_28_no_next_authorization(self):
        self.assertEqual(self.data['NEXT_TIER_AUTHORIZATION_STATUS'],'NOT_AUTHORIZED')
        for key in ('R4','R5','R6'):
            self.assertEqual(self.data[key],'NOT_EXECUTED')

    def test_29_two_independent_worker_processes(self):
        with tempfile.TemporaryDirectory(prefix='er2-r3a1-test-') as temp:
            values=[]
            for i in (1,2):
                path=Path(temp)/f'worker{i}.json'
                subprocess.run([sys.executable,str(a.ROOT/a.SCRIPT),'--synthetic-worker',str(path)],cwd=a.ROOT,check=True)
                values.append(path.read_bytes())
            self.assertEqual(values[0],values[1])
            self.assertEqual(json.loads(values[0]),self.data)

    def test_30_canonical_outputs_and_non_circular_hash(self):
        suite={'counts':{'run':0}}
        payloads=a.render(self.data,{'status':'PASS'},suite)
        self.assertEqual(set(payloads),{a.JSON,a.REPORT,a.CERT})
        for value in payloads.values():
            value.decode('utf-8')
            self.assertNotIn(b'\r',value)
            self.assertFalse(value.startswith(b'\xef\xbb\xbf'))
            self.assertTrue(value.endswith(b'\n'))
            self.assertFalse(value.endswith(b'\n\n'))
            self.assertNotIn(str(a.ROOT).encode(),value)
        certified=json.loads(payloads[a.CERT])
        self.assertNotIn(a.CERT,certified['artifact_sha256'])
        self.assertTrue(certified['R3A_ADAPTER_VALIDATED'])

    def test_31_hold_cannot_create_certified_lock(self):
        data=copy.deepcopy(self.data)
        data['final_verdict']=a.HOLD_E
        self.assertNotIn(a.CERT,a.render(data,{'status':'PASS'},{'counts':{}}))

    def test_32_uncertified_suite_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'suite.json'
            path.write_bytes(r.json_bytes({'unrelated_real_regressions':1,'unresolved':0}))
            with self.assertRaisesRegex(RuntimeError,'FAIL_TEST_REGRESSION'):
                a.build(Path(temp)/'outputs',path)

    def test_33_all_scientific_gates_pass(self):
        self.assertEqual(self.data['final_verdict'],a.PASS)
        self.assertIs(self.data['R3A_ADAPTER_VALIDATED'],True)

    def test_34_frozen_dependencies_unchanged(self):
        self.assertFalse(r.git('diff','--name-only','HEAD').strip())
        self.assertEqual(r.sha((r.ROOT/'scripts/econometric_design_master_v1.py').read_bytes()),r.ED1_SHA)


if __name__=='__main__':
    unittest.main(verbosity=2)
