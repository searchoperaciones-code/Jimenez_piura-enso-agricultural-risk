from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import er2_r3_named_wcr_adapter_v1 as r


class R3AAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.validate()
        cls.positions = cls.data['positional_validation']
        cls.columns = cls.data['target_map'][0]['FROZEN_REGRESSORS']
        cls.frame,cls.y = r.synthetic_panel(cls.columns)

    def test_01_exact_parent(self):
        self.assertEqual(self.data['preflight']['parent'],'611c91255d5a367127df57dd69855e2df83ac0cb')

    def test_02_exact_predecessor_lock(self):
        self.assertEqual(self.data['preflight']['r2_reporting_lock_sha256'],r.CERT_SHA)

    def test_03_exact_r3_contract_hash(self):
        self.assertEqual(r.sha(r.json_bytes(self.data['preflight']['future_real_contract'])),r.TIER_SHA)

    def test_04_exact_frozen_future_determinism(self):
        contract = self.data['preflight']['future_real_contract']
        self.assertEqual((contract['seed'],contract['replications'],contract['determinism']['batch_size']),(20260903,9999,1000))
        self.assertEqual(contract['weights'],'RADEMACHER')
        self.assertEqual(contract['determinism']['rng'],'NUMPY_GENERATOR_PCG64')
        self.assertEqual(contract['determinism']['seed_reset'],'EACH_CROP_CONTRAST_AND_JOINT_TEST')

    def test_05_no_real_outcomes(self):
        self.assertIs(self.data['REAL_OUTCOME_VALUES_READ'],False)
        with r.outcome_firewall(), self.assertRaises(r.RealOutcomeFirewall):
            (r.ROOT/'data/processed/panel_master.csv').read_bytes()

    def test_06_transient_outcome_firewall(self):
        with r.outcome_firewall(), self.assertRaises(r.RealOutcomeFirewall):
            (r.ROOT/'data/processed/outcomes/transient_campaign_outcomes_master.csv').read_bytes()

    def test_07_frozen_real_loaders_blocked(self):
        with r.outcome_firewall():
            for loader in (r.ed1.read_transient_primary,r.ed1.read_perennial_primary,r.ed1.read_b3_sensitivity):
                with self.assertRaises(r.RealOutcomeFirewall):
                    loader()

    def test_08_real_execution_zero(self):
        self.assertIs(self.data['REAL_R3_EXECUTED'],False)
        self.assertEqual(self.data['REAL_R3_MODELS_EXECUTED'],0)
        self.assertEqual(self.data['REAL_BOOTSTRAP_REPLICATIONS_EXECUTED'],0)

    def test_09_exact_target_names_outcome_blind(self):
        base = ['RAIN_ANOM_MM','TMAX_ANOM_C','TMIN_ANOM_C']
        expected = {code:base for code in ('14010020000','14010070000','13010210000')}
        expected.update({code:[name+suffix for suffix in ('__T','__T_MINUS_1') for name in base]
                         for code in ('13010170102','15010040000')})
        observed = {code:[row['VARIABLE'] for row in self.data['target_map'] if row['CROP_CODE']==code] for code in expected}
        self.assertEqual(observed,expected)

    def test_10_architecture_sizes(self):
        self.assertEqual(sorted(Counter(row['CROP_CODE'] for row in self.data['target_map']).values()),[3,3,3,6,6])

    def test_11_no_duplicate_targets(self):
        self.assertEqual(len({(row['CROP_CODE'],row['VARIABLE']) for row in self.data['target_map']}),21)

    def test_12_every_position_tested(self):
        self.assertEqual(set(self.positions),{f'{size}:{j}' for size in (3,6) for j in range(size)})

    def test_13_full_model_preserved(self):
        self.assertTrue(all(v['full_regressor_set_preserved'] for v in self.positions.values()))
        self.assertTrue(all(v['frame_response_unchanged'] for v in self.positions.values()))

    def test_14_every_permutation_inverse(self):
        for row in self.data['target_map']:
            original = row['FROZEN_REGRESSORS']
            reordered = [original[i] for i in row['PERMUTATION']]
            self.assertEqual(reordered[0],row['VARIABLE'])
            self.assertEqual([reordered[i] for i in row['INVERSE_PERMUTATION']],original)
            self.assertEqual(reordered[1:],[v for v in original if v!=row['VARIABLE']])

    def test_15_bad_target_and_duplicates_rejected(self):
        for columns,target in [(['a','b'],'c'),(['a','a'],'a'),([],'a')]:
            with self.assertRaises(ValueError):
                r.permutation(columns,target)

    def test_16_synthetic_seed_prespecified_distinct(self):
        self.assertEqual(r.SYNTHETIC_SPEC['data_seed'],2026090501)
        self.assertNotEqual(r.SYNTHETIC_SPEC['data_seed'],20260903)
        self.assertEqual(self.data['synthetic_specification_sha256'],r.sha(r.json_bytes(r.SYNTHETIC_SPEC)))

    def test_17_synthetic_two_builds_identical(self):
        frame,y = r.synthetic_panel(self.columns)
        self.assertTrue(frame.equals(self.frame))
        np.testing.assert_array_equal(y,self.y)
        self.assertTrue(all(v['data_generation_twice_exact'] for v in self.data['synthetic_identities'].values()))

    def test_18_synthetic_architecture_full_rank(self):
        for size in (3,6):
            columns = next(v['FROZEN_REGRESSORS'] for v in self.data['target_map'] if v['ARCHITECTURE']==size)
            frame,y = r.synthetic_panel(columns)
            fe = r.ed1.fe_matrix(frame,'PERIOD')
            x = r.ed1.absorb_fixed_effects(frame[columns].to_numpy(),fe)
            self.assertEqual(np.linalg.matrix_rank(x),size)
            self.assertEqual(len(y),128)
        self.assertEqual(len(set(abs(v) for v in r.SYNTHETIC_SPEC['beta'])),6)
        self.assertGreater(r.SYNTHETIC_SPEC['noise_ar1'],0)
        self.assertGreater(r.SYNTHETIC_SPEC['cluster_time_slope_scale'],0)

    def test_19_fixed_machine_tolerance(self):
        self.assertEqual(r.SYNTHETIC_SPEC['absolute_tolerance'],1e-10)
        self.assertEqual(r.SYNTHETIC_SPEC['relative_tolerance'],1e-10)
        self.assertIs(r.SYNTHETIC_SPEC['exact_observed_statistic_gate'],True)

    def test_20_beta_fitted_residual_cr2_t_equivalence(self):
        for value in self.positions.values():
            self.assertTrue(value['A_B']['numerical_tolerance_pass'])
            self.assertTrue(value['A_C']['numerical_tolerance_pass'])
            self.assertEqual(set(value['A_C']['max_absolute_errors']),
                             {'beta','fitted','residual','cr2_covariance','observed_statistic','restricted_residual'})

    def test_21_named_explicit_path_exact(self):
        for value in self.positions.values():
            self.assertEqual(value['A'],value['B'])
            self.assertEqual(value['A_B']['status'],'PASS')

    def test_22_same_cluster_assignment(self):
        self.assertTrue(all(v[path]['cluster_assignment_exact'] for v in self.positions.values() for path in ('A_B','A_C')))

    def test_23_same_draws_and_pcg64_states(self):
        for value in self.positions.values():
            self.assertTrue(value['A_C']['draws_rng_batches_exact'])
            for key in ('draw_sha256','final_pcg64_state'):
                self.assertEqual(value['A'][key],value['B'][key])
                self.assertEqual(value['A'][key],value['C'][key])

    def test_24_partial_final_batch(self):
        for value in self.positions.values():
            for path in ('A','B','C'):
                self.assertEqual(value[path]['batch_partition'],[1000,1000,1])

    def test_25_exact_exceedances(self):
        for value in self.positions.values():
            self.assertEqual(value['A']['exceedances'],value['B']['exceedances'])
            self.assertEqual(value['A']['exceedances'],value['C']['exceedances'])

    def test_26_exact_finite_correction(self):
        for value in self.positions.values():
            for path in ('A','B','C'):
                self.assertEqual(value[path]['exact_finite_p'],(1+value[path]['exceedances'])/2002)

    def test_27_correction_edges_and_bad_counts(self):
        self.assertEqual(r.finite_p(0,2001),1/2002)
        self.assertEqual(r.finite_p(2001,2001),1.)
        for exceed,b in [(-1,3),(4,3),(0,0),(0.5,3)]:
            with self.assertRaises(ValueError):
                r.finite_p(exceed,b)

    def test_28_valid_designs_zero_invalid(self):
        self.assertEqual(self.data['invalid_replications'],0)

    def test_29_invalid_replication_propagates_hold(self):
        fake = {'frozen_result':{'invalid_replications':1},'invalid_replications':1}
        with patch.object(r,'frozen_wcr_audit',return_value=fake) as engine:
            value = r.named_coefficient_wcr_adapter(self.frame,self.columns,'PERIOD',self.y,self.columns[1],2001,20260903)
        self.assertEqual(value['tier_status'],'HOLD')
        self.assertEqual(value['invalid_replications'],1)
        engine.assert_called_once()
        self.assertEqual(r.tier_status(1),'HOLD')
        self.assertEqual(r.tier_status(0),'COMPLETE')

    def test_30_no_drop_redraw_or_denominator_reduction(self):
        self.assertEqual(self.data['INVALID_REPLICATION_FIREWALL'],'HOLD_NO_DROP_NO_REDRAW_NO_DENOMINATOR_CHANGE')
        fake = {'frozen_result':{'invalid_replications':2,'replications':2001},'invalid_replications':2}
        with patch.object(r,'frozen_wcr_audit',return_value=fake) as engine:
            out = r.named_coefficient_wcr_adapter(self.frame,self.columns,'PERIOD',self.y,self.columns[0],2001,20260903)
        self.assertEqual(engine.call_count,1)
        self.assertEqual(out['frozen_wcr_result']['replications'],2001)

    def test_31_joint_numerical_noninterference(self):
        for value in self.data['joint_validation'].values():
            self.assertTrue(value['comparison']['numerical_tolerance_pass'])
            self.assertTrue(value['comparison']['exceedances_invalid_exact'])
            self.assertTrue(value['comparison']['finite_p_exact'])
            self.assertTrue(value['comparison']['draws_rng_batches_exact'])

    def test_32_holm_grouping_only(self):
        self.assertEqual(self.data['holm_family_sizes'],[3,3,3,6,6])
        self.assertEqual(self.data['R3_MULTIPLICITY'],'HOLM_STEP_DOWN_WITHIN_CROP_WCR_COEFFICIENT_P_VALUES')
        self.assertIs(self.data['real_holm_calculated'],False)

    def test_33_no_result_specific_branches(self):
        self.assertEqual(r.branch_audit()['result_specific_adapter_branches'],0)

    def test_34_independent_reference_has_no_ed1_or_adapter_call(self):
        source = r.inspect.getsource(r.one_hot_reference)
        tree = ast.parse(source)
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any('ed1.' in name or 'adapter' in name or 'frozen_wcr' in name for name in calls))

    def test_35_real_values_not_copied(self):
        self.assertIs(self.data['PRIMARY_RESULTS_VALUES_COPIED'],False)
        self.assertIs(self.data['R2_RESULTS_VALUES_COPIED'],False)
        self.assertNotIn('coefficient_inventory',self.data)

    def test_36_no_real_cli(self):
        tree = ast.parse(r.inspect.getsource(r.main))
        flags = [n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('--')]
        self.assertEqual(set(flags),{'--output-root','--synthetic-worker'})

    def test_37_no_next_tier_authorization(self):
        self.assertEqual(self.data['NEXT_TIER_AUTHORIZATION_STATUS'],'NOT_AUTHORIZED')
        for tier in ('R4','R5','R6'):
            self.assertEqual(self.data[tier],'NOT_EXECUTED')

    def test_38_exact_gate_cannot_be_replaced_by_tolerance(self):
        expected = all(v['verdict']==r.PASS for v in self.positions.values()) and all(
            v['comparison']['status']=='PASS' for v in self.data['joint_validation'].values())
        self.assertEqual(self.data['R3_ADAPTER_VALIDATED'],expected)
        for v in self.positions.values():
            if not v['A_C']['observed_statistic_exact']:
                self.assertEqual(v['verdict'],r.HOLD)

    def test_39_deterministic_render(self):
        with tempfile.TemporaryDirectory(prefix='er2-r3a-test-build-') as temp:
            built = r.build(Path(temp))
            rep = built['reproducibility']
            self.assertEqual(rep['independent_processes'],2)
            self.assertEqual(rep['run1_sha256'],rep['run2_sha256'])
            self.assertTrue(rep['all_rendered_outputs_exact'])
            for path,payload in r.render(json.loads(r.json_bytes(self.data)),rep).items():
                self.assertEqual((Path(temp)/path).read_bytes(),payload)

    def test_40_byte_contract(self):
        for value in r.render(self.data,{'status':'PASS'}).values():
            value.decode('utf-8')
            self.assertNotIn(b'\r',value)
            self.assertFalse(value.startswith(b'\xef\xbb\xbf'))
            self.assertTrue(value.endswith(b'\n'))
            self.assertFalse(value.endswith(b'\n\n'))

    def test_41_no_time_or_absolute_local_paths(self):
        for value in r.render(self.data,{'status':'PASS'}).values():
            self.assertNotIn(str(r.ROOT).encode(),value)
            self.assertNotIn(b'generated_at',value)
            self.assertNotIn(b'timestamp',r.json_bytes(self.data))

    def test_42_target_ledger_has_21_rows(self):
        payload = r.render(self.data,{'status':'PASS'})[r.CSV]
        rows = list(r.csv.DictReader(r.io.StringIO(payload.decode())))
        self.assertEqual(len(rows),21)
        self.assertTrue(all(row['REAL_OUTCOME_EXECUTION_STATUS']=='NOT_EXECUTED' for row in rows))

    def test_43_non_circular_lock_hash(self):
        locked = json.loads(r.render(self.data,{'status':'PASS'})[r.LOCK])
        self.assertNotIn(r.LOCK,locked['artifact_sha256'])

    def test_44_no_overwrite_and_no_identical_rewrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fixture.txt'
            r.write_exact(path,b'fixture\n')
            before = path.stat().st_mtime_ns
            r.write_exact(path,b'fixture\n')
            self.assertEqual(path.stat().st_mtime_ns,before)
            with self.assertRaises(RuntimeError):
                r.write_exact(path,b'changed\n')

    def test_45_noncanonical_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for b in (b'x\r\n',b'\xef\xbb\xbfx\n',b'x',b'x\n\n'):
                with self.assertRaises(ValueError):
                    r.write_exact(Path(temp)/'fixture',b)

    def test_46_alignment_and_batch_contract(self):
        with self.assertRaises(ValueError):
            r.named_coefficient_wcr_adapter(self.frame.iloc[::-1],self.columns,'PERIOD',self.y,self.columns[0],2001,20260903)
        with self.assertRaises(ValueError):
            r.named_coefficient_wcr_adapter(self.frame,self.columns,'PERIOD',self.y,self.columns[0],2001,20260903,999)
        with self.assertRaises(ValueError):
            r.named_coefficient_wcr_adapter(self.frame,self.columns,'PERIOD',self.y[:,None],self.columns[0])

    def test_47_wrong_parent_rejected(self):
        with patch.object(r,'git',return_value=b'wrong\n'),self.assertRaisesRegex(RuntimeError,'UPSTREAM_IMMUTABILITY'):
            r.preflight()

    def test_48_zero_frozen_source_mutation(self):
        self.assertEqual(hashlib.sha256((r.ROOT/'scripts/econometric_design_master_v1.py').read_bytes()).hexdigest(),r.ED1_SHA)
        self.assertEqual(r.git('diff','--name-only','HEAD').strip(),b'')


if __name__=='__main__':
    unittest.main(verbosity=2)
