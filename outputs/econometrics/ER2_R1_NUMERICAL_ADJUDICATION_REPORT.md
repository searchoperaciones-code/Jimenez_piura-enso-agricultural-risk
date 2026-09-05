# ER2 R1A Numerical Adjudication v1

FINAL_VERDICT=ER2_R1A_PASS_NUMERICAL_ROUNDOFF_ADJUDICATED_READY_FOR_R1_FREEZE_DECISION

The seven original R1 files and the provisional failure lock are immutable. No result table, specification, tolerance or historical test is replaced.
The historical absolute 1e-8 rule is an alarm across heterogeneous units, not a scale-free distance; it remains FAIL_PRESERVED, not incorrect or erased.
R2-R6 remain unauthorized and unexecuted. No path averaging, result selection, or new significance criterion.

## Numerical environment

```json
{
  "build_configurations": {
    "numpy": {
      "blas_lapack": {
        "blas": {
          "detection method": "pkgconfig",
          "found": true,
          "name": "scipy-openblas",
          "openblas configuration": "OpenBLAS 0.3.30  USE64BITINT DYNAMIC_ARCH NO_AFFINITY SkylakeX MAX_THREADS=24",
          "version": "0.3.30"
        },
        "lapack": {
          "detection method": "pkgconfig",
          "found": true,
          "name": "scipy-openblas",
          "openblas configuration": "OpenBLAS 0.3.30  USE64BITINT DYNAMIC_ARCH NO_AFFINITY SkylakeX MAX_THREADS=24",
          "version": "0.3.30"
        }
      },
      "compilers": {
        "c": {
          "commands": "cl",
          "linker": "link",
          "name": "msvc",
          "version": "19.44.35219"
        },
        "c++": {
          "commands": "cl",
          "linker": "link",
          "name": "msvc",
          "version": "19.44.35219"
        },
        "cython": {
          "commands": "cython",
          "linker": "cython",
          "name": "cython",
          "version": "3.2.1"
        }
      },
      "full_build_configuration_sha256": "c77f4ec87d415df79fc74181a708c5c4e750eb8d064c7d192cb3cc5c3cf91ab7",
      "machine_information": {
        "build": {
          "cpu": "x86_64",
          "endian": "little",
          "family": "x86_64",
          "system": "windows"
        },
        "host": {
          "cpu": "x86_64",
          "endian": "little",
          "family": "x86_64",
          "system": "windows"
        }
      }
    },
    "scipy": {
      "blas_lapack": {
        "blas": {
          "detection method": "pkgconfig",
          "found": true,
          "name": "scipy-openblas",
          "openblas configuration": "OpenBLAS 0.3.29.dev DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=24",
          "version": "0.3.29.dev"
        },
        "lapack": {
          "detection method": "pkgconfig",
          "found": true,
          "name": "scipy-openblas",
          "openblas configuration": "OpenBLAS 0.3.29.dev DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=24",
          "version": "0.3.29.dev"
        }
      },
      "compilers": {
        "c": {
          "commands": "cc",
          "linker": "ld.bfd",
          "name": "gcc",
          "version": "10.3.0"
        },
        "c++": {
          "commands": "c++",
          "linker": "ld.bfd",
          "name": "gcc",
          "version": "10.3.0"
        },
        "cython": {
          "commands": "cython",
          "linker": "cython",
          "name": "cython",
          "version": "3.1.6"
        },
        "fortran": {
          "commands": "gfortran",
          "linker": "ld.bfd",
          "name": "gcc",
          "version": "10.3.0"
        },
        "pythran": {
          "version": "0.18.0"
        }
      },
      "full_build_configuration_sha256": "957f423a8bdd9d1e6fda5d66d139c0fcb1acd7defe3013a1609c3e3710c66a27",
      "machine_information": {
        "build": {
          "cpu": "x86_64",
          "endian": "little",
          "family": "x86_64",
          "system": "windows"
        },
        "cross-compiled": false,
        "host": {
          "cpu": "x86_64",
          "endian": "little",
          "family": "x86_64",
          "system": "windows"
        }
      }
    }
  },
  "cpu_architecture": "AMD64",
  "cpu_processor": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel",
  "environment_changed": false,
  "eps": 2.220446049250313e-16,
  "floating_type": "IEEE754_BINARY64_NUMPY_FLOAT64",
  "non_numerical_build_paths": "OMITTED_CONFIGURATION_HASH_PRESERVES_IDENTITY",
  "numpy": "2.3.5",
  "observable_blas_pools": [
    {
      "active_threads": 16,
      "library": "libscipy_openblas64_-9e3e5a4229c1ca39f10dc82bba9e2b2b.dll",
      "observation_symbol": "scipy_openblas_get_num_threads64_",
      "package": "numpy"
    },
    {
      "active_threads": 16,
      "library": "libscipy_openblas-48c358d105077551cc9cc3ba79387ed5.dll",
      "observation_symbol": "scipy_openblas_get_num_threads",
      "package": "scipy"
    }
  ],
  "optional_r_reference": "NOT_RUN_RSCRIPT_NOT_ON_PATH",
  "packages_installed": false,
  "python": "3.11.7",
  "scipy": "1.16.3",
  "thread_environment": {
    "BLIS_NUM_THREADS": null,
    "GOTO_NUM_THREADS": null,
    "MKL_NUM_THREADS": null,
    "NUMEXPR_NUM_THREADS": null,
    "OMP_NUM_THREADS": null,
    "OPENBLAS_NUM_THREADS": null,
    "VECLIB_MAXIMUM_THREADS": null
  },
  "tiny": 2.2250738585072014e-308
}
```

## Prespecified adjudication policy

```json
{
  "aht_scalar_relative": 1e-06,
  "beta_relative_l2": 1e-10,
  "coefficient_rounding": "12_SIGNIFICANT_DIGITS_FIXED_BEFORE_THIRD_PATH",
  "conditioning_budget_interpretation": "NORMWISE_ERROR_AMPLIFICATION_DIAGNOSTIC_NOT_A_RIGOROUS_END_TO_END_CR2_FORWARD_ERROR_BOUND",
  "conditioning_consistency_budget": "ETA/(1-ETA); ETA=COND2(Z_TRANSPOSE_Z)*GAMMA_N; GAMMA_N=N*EPS/(1-N*EPS); REQUIRE_ETA_LT_1",
  "covariance_relative_frobenius": 1e-06,
  "df_f_p_rounding": "6_DECIMAL_PLACES_DESCRIPTIVE_NOT_A_PASS_GATE",
  "df_relative_l2_and_each_coefficient": 1e-06,
  "no_p_value_selection": true,
  "perennial_drift_rule": "STABLE_QR_LEVEL_VS_ANOMALY_MUST_PASS_DIRECTOR_ENVELOPE; LEGACY_DRIFT_MUST_BE_CONDITIONING_CONSISTENT_WITH_NO_RANK_OR_SINGULARITY_CHANGE",
  "qr_rank_rcond": 1e-12,
  "source_representation_bound": "128*FLOAT64_EPS*MAX_ABS_PAIRED_SOURCE_VALUE_OR_1_PER_COLUMN",
  "strict_legacy_rule": "ABSOLUTE_1E-8_ALARM_REMAINS_FAIL_PRESERVED",
  "tiny": 2.2250738585072014e-308
}
```

The third path uses explicit district/period FE, deterministic column L2 scaling, pivoted QR, triangular solves and back-transformation to original units. CR2 is reconstructed directly from cluster influence matrices; HTZ uses Cholesky whitening and cluster-pair traces.
References: [SciPy pivoted QR](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.qr.html); [clubSandwich HTZ](https://jepusto.github.io/clubSandwich/reference/Wald_test.html).

## RICE

THREE_PATH_STATUS=PASS
Strict historical discrepancies reproduce exactly: {"aht_denominator_df_max_abs_difference": 2.1799451133119874e-11, "aht_f_max_abs_difference": 3.831810202470365e-09, "aht_p_max_abs_difference": 1.641895397419546e-09, "beta_max_abs_difference": 4.8155923693116165e-15, "cr2_covariance_max_abs_difference": 5.295131520755003e-11, "satterthwaite_df_max_abs_difference": 1.494845491833985e-08}

MAIN_VS_SVD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 1.7240507446623634e-12, "aht_f_statistic_symmetric_relative": 3.9609155508979395e-09, "aht_p_value_symmetric_relative": 3.7454754445223736e-09, "beta_relative_l2": 3.564898001170222e-14, "cr2_covariance_relative_frobenius": 1.9566573372828303e-09, "satterthwaite_df_max_component_relative": 6.962442051009296e-10, "satterthwaite_df_relative_l2": 5.176261255789664e-10}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
MAIN_VS_THIRD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 1.7439998324835522e-12, "aht_f_statistic_symmetric_relative": 3.961246756861946e-09, "aht_p_value_symmetric_relative": 3.745789237344383e-09, "beta_relative_l2": 2.652552285192477e-14, "cr2_covariance_relative_frobenius": 1.9566542853815695e-09, "satterthwaite_df_max_component_relative": 6.962514858853511e-10, "satterthwaite_df_relative_l2": 5.176320245330321e-10}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
SVD_VS_THIRD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 1.994908782122317e-14, "aht_f_statistic_symmetric_relative": 3.3120596531886876e-13, "aht_p_value_symmetric_relative": 3.137928231845456e-13, "beta_relative_l2": 1.0263336030143133e-14, "cr2_covariance_relative_frobenius": 2.1852694503668497e-14, "satterthwaite_df_max_component_relative": 3.072894326885831e-14, "satterthwaite_df_relative_l2": 1.1123358992161383e-14}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
MAIN: condition(within X)=170.904635098; condition(Z)=8148.60055489; condition(Z'Z)=66399690.9967; bread drift=2.58654001131e-09.
SVD: condition(within X)=170.904635098; condition(Z)=8148.60055489; condition(Z'Z)=66399690.9967; bread drift=0.
Reporting invariance (descriptive only): {"aht_numerical_result": true, "beta12_significant_digits": false, "ci_zero_inclusion": true, "coefficient_df6": true, "coefficient_sign": true, "effective_df_flags": true, "holm_ordering": true}

## MAIZ_AMARILLO_DURO

THREE_PATH_STATUS=PASS
Strict historical discrepancies reproduce exactly: {"aht_denominator_df_max_abs_difference": 1.7073276126211567e-09, "aht_f_max_abs_difference": 1.1348567974245327e-07, "aht_p_max_abs_difference": 1.8368687348946366e-08, "beta_max_abs_difference": 2.5709989692757063e-13, "cr2_covariance_max_abs_difference": 6.254811460437715e-10, "satterthwaite_df_max_abs_difference": 1.6831963378649561e-07}

MAIN_VS_SVD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 6.159487832923464e-11, "aht_f_statistic_symmetric_relative": 5.903452439668506e-08, "aht_p_value_symmetric_relative": 1.2318568223869742e-07, "beta_relative_l2": 1.3132790360762657e-12, "cr2_covariance_relative_frobenius": 2.9155995329873446e-08, "satterthwaite_df_max_component_relative": 6.103515916390862e-09, "satterthwaite_df_relative_l2": 3.773034078611292e-09}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
MAIN_VS_THIRD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 6.166152696883179e-11, "aht_f_statistic_symmetric_relative": 5.9034531558067967e-08, "aht_p_value_symmetric_relative": 1.231856850307501e-07, "beta_relative_l2": 1.3227641437143273e-12, "cr2_covariance_relative_frobenius": 2.9156042357287695e-08, "satterthwaite_df_max_component_relative": 6.103621940674599e-09, "satterthwaite_df_relative_l2": 3.7730839481957615e-09}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
SVD_VS_THIRD: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 6.664863960125446e-14, "aht_f_statistic_symmetric_relative": 7.16138332108092e-15, "aht_p_value_symmetric_relative": 2.7920530256491477e-15, "beta_relative_l2": 9.799717470909577e-15, "cr2_covariance_relative_frobenius": 5.1067997878103526e-14, "satterthwaite_df_max_component_relative": 1.0602428438422162e-13, "satterthwaite_df_relative_l2": 8.792001045855252e-14}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
MAIN: condition(within X)=764.428825221; condition(Z)=34203.6688723; condition(Z'Z)=1169890964.29; bread drift=2.68640467338e-08.
SVD: condition(within X)=764.428825221; condition(Z)=34203.6688723; condition(Z'Z)=1169890964.29; bread drift=0.
Reporting invariance (descriptive only): {"aht_numerical_result": true, "beta12_significant_digits": false, "ci_zero_inclusion": true, "coefficient_df6": true, "coefficient_sign": true, "effective_df_flags": true, "holm_ordering": true}

## Perennial 13010210000

ALGEBRA=ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT
Original float64 nonexact status is preserved; distinct evidence contribution remains zero.
Projection maximum absolute residual: 2.842170943040401e-14
The exposure difference is tested against district constants at source representation precision. If LEVEL=ANOMALY+district constant, M_FE annihilates that constant in exact arithmetic, preserving slopes and fitted values after FE reparameterization.

Legacy downstream relative discrepancies: {"aht_denominator_df_symmetric_relative": 3.3746792737834357e-13, "aht_f_statistic_symmetric_relative": 2.9298828344424366e-09, "aht_p_value_symmetric_relative": 9.659700314685184e-10, "coefficient_inference_vector_relative_l2": 5.777704518724963e-10, "cr2_covariance_relative_frobenius": 1.6672998038242127e-09, "satterthwaite_df_max_component_relative": 2.7319327841964574e-10, "satterthwaite_df_relative_l2": 1.778993806175206e-10}
Original absolute discrepancies: {"aht": 3.5777134588244053e-09, "coefficient_inference": 1.3984200464278729e-09, "coefficients": 4.707345624410664e-14, "cr2_covariance": 1.1127576637903758e-09, "fitted_values": 9.64561763794336e-13, "residuals": 9.64561763794336e-13, "satterthwaite_df": 5.392195134845679e-09, "transformed_x": 1.758593271006248e-13}
Stable QR LEVEL/anomaly: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 3.178038162481045e-15, "aht_f_statistic_symmetric_relative": 5.589075202629635e-13, "aht_p_value_symmetric_relative": 1.851526472768932e-13, "beta_relative_l2": 3.292534354009036e-13, "cr2_covariance_relative_frobenius": 5.581607096947061e-14, "satterthwaite_df_max_component_relative": 1.838282556953035e-14, "satterthwaite_df_relative_l2": 1.2349884109958572e-14}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
Drift gates: {"error_amplification_consistency": true, "legacy_rank_and_singularity_agreement": true, "no_normal_equation_rank_loss": true, "stable_qr_equivalence": true}
Interpretation: CONSISTENT_WITH_FLOAT64_ERROR_AMPLIFICATION

## Perennial 13010170102

ALGEBRA=ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT
Original float64 nonexact status is preserved; distinct evidence contribution remains zero.
Projection maximum absolute residual: 5.684341886080801e-13
The exposure difference is tested against district constants at source representation precision. If LEVEL=ANOMALY+district constant, M_FE annihilates that constant in exact arithmetic, preserving slopes and fitted values after FE reparameterization.

Legacy downstream relative discrepancies: {"aht_denominator_df_symmetric_relative": 2.0557652740039877e-08, "aht_f_statistic_symmetric_relative": 1.018417231218938e-06, "aht_p_value_symmetric_relative": 2.1210308815702575e-06, "coefficient_inference_vector_relative_l2": 8.487440446707806e-06, "cr2_covariance_relative_frobenius": 2.988087746124908e-05, "satterthwaite_df_max_component_relative": 5.726598014329881e-06, "satterthwaite_df_relative_l2": 2.9866187466072285e-06}
Original absolute discrepancies: {"aht": 1.0663690794388003e-05, "coefficient_inference": 5.1661600248387174e-05, "coefficients": 1.9240165016753963e-13, "cr2_covariance": 7.062535648039159e-05, "fitted_values": 1.4246381851990009e-11, "residuals": 1.4246381851990009e-11, "satterthwaite_df": 0.00014480159220653377, "transformed_x": 4.376943252282217e-12}
Stable QR LEVEL/anomaly: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 2.2534543161900665e-15, "aht_f_statistic_symmetric_relative": 2.4439537818170277e-14, "aht_p_value_symmetric_relative": 5.094016938402485e-14, "beta_relative_l2": 1.7862079155043862e-14, "cr2_covariance_relative_frobenius": 2.8340088248134638e-14, "satterthwaite_df_max_component_relative": 9.554159380688409e-15, "satterthwaite_df_relative_l2": 6.884144659452991e-15}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
Drift gates: {"error_amplification_consistency": true, "legacy_rank_and_singularity_agreement": true, "no_normal_equation_rank_loss": true, "stable_qr_equivalence": true}
Interpretation: CONSISTENT_WITH_FLOAT64_ERROR_AMPLIFICATION

## Perennial 15010040000

ALGEBRA=ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT
Original float64 nonexact status is preserved; distinct evidence contribution remains zero.
Projection maximum absolute residual: 5.684341886080801e-13
The exposure difference is tested against district constants at source representation precision. If LEVEL=ANOMALY+district constant, M_FE annihilates that constant in exact arithmetic, preserving slopes and fitted values after FE reparameterization.

Legacy downstream relative discrepancies: {"aht_denominator_df_symmetric_relative": 1.887170499025491e-09, "aht_f_statistic_symmetric_relative": 1.205655504681373e-06, "aht_p_value_symmetric_relative": 5.387592238958564e-06, "coefficient_inference_vector_relative_l2": 2.0375828666711653e-06, "cr2_covariance_relative_frobenius": 8.744552267195387e-06, "satterthwaite_df_max_component_relative": 1.3780251398522994e-06, "satterthwaite_df_relative_l2": 7.560856542171881e-07}
Original absolute discrepancies: {"aht": 2.4601733620954747e-05, "coefficient_inference": 1.4360656972911556e-05, "coefficients": 1.269206961751479e-12, "cr2_covariance": 3.180169638028474e-05, "fitted_values": 4.702283007418373e-11, "residuals": 4.702283007418373e-11, "satterthwaite_df": 4.034808660691169e-05, "transformed_x": 6.366462912410498e-12}
Stable QR LEVEL/anomaly: {"cr2_singularity_status_agreement": true, "metrics": {"aht_denominator_df_symmetric_relative": 1.4230236047837258e-15, "aht_f_statistic_symmetric_relative": 9.247032163302104e-14, "aht_p_value_symmetric_relative": 4.1273787860389805e-13, "beta_relative_l2": 9.313485095433645e-14, "cr2_covariance_relative_frobenius": 5.4135957498048714e-14, "satterthwaite_df_max_component_relative": 1.8891617924564035e-14, "satterthwaite_df_relative_l2": 1.1673526503442256e-14}, "nonfinite_count": 0, "rank_agreement": true, "sign_agreement": true, "status": "PASS"}
Drift gates: {"error_amplification_consistency": true, "legacy_rank_and_singularity_agreement": true, "no_normal_equation_rank_loss": true, "stable_qr_equivalence": true}
Interpretation: CONSISTENT_WITH_FLOAT64_ERROR_AMPLIFICATION

## Certification and provenance

The JSON records full spectra, CR2 block eigenvalues, AHT conditioning, all pairwise numerical distances and reporting objects. The conditioning budget is a diagnostic scale for amplification, not a rigorous end-to-end error guarantee.
Original R1 result CSV hashes remain the scientific result identities; QR results are verification only.
R1_FIRST_ATTEMPT_PROVISIONAL_FAILURE_LOCK_SHA256=c7ae05b96b4155df5fe1d74484784c02c7fe32084b443aa7a02107b37a5c1963
CERTIFIED_LOCK_CREATION_AUTHORIZED_BY_ADJUDICATION=TRUE
NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED

NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_FREEZE_DECISION_IF_PASS
