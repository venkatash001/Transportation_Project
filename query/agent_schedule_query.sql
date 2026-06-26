-- CES IND Transport Roster - Agent Schedule Query
-- Fix: CTE deduplicates CS_AGNT first (one row per agent, best WIN/L1 row wins)
-- before joining to CS_AGNT_SCHED, so GROUP BY never sees NULL vs non-NULL
-- splits for the same agent.

WITH AGNT_BEST AS (
    -- For each VCC_AGNT_ID, keep exactly ONE row.
    -- Priority: rows where LVL1_MGR_LOGIN_NM is populated first,
    --           then rows where WIN_NBR is populated (WIN_NBR is INT64 - no TRIM).
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY VCC_AGNT_ID
            ORDER BY
                CASE WHEN LVL1_MGR_LOGIN_NM IS NOT NULL
                          AND LVL1_MGR_LOGIN_NM != ''   THEN 0 ELSE 1 END,
                CASE WHEN WIN_NBR IS NOT NULL
                          AND WIN_NBR > 0               THEN 0 ELSE 1 END
        ) AS _rn
    FROM `wmt-cc-datasphere-prod.WFM_ADHOC.CS_AGNT`
)

SELECT
    S.SRC_APPLN_NM AS Source_Application_Name,
    S.AGNT_ACCT_ID AS VCC_ID,

    -- Agent Details from CS_AGNT (deduplicated)
    A.LOGIN_ID,
    A.WIN_NBR,
    A.AGNT_PROFL_NM,
    A.FIRST_NM,
    A.LAST_NM,
    A.EMAIL_ADDR_TXT,
    A.CNTCT_CHNL_NM,
    A.LVL1_MGR_LOGIN_ID,
    A.LVL1_MGR_LOGIN_NM,
    A.LVL2_MGR_LOGIN_ID,
    A.LVL2_MGR_LOGIN_NM,
    A.BUS_LINE_NM,
    A.BUS_SUB_LINE_NM,

    S.SITE_NM AS Team_Name,
    S.GEO_REGION_CD AS Geo_Location,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        DATETIME(TIMESTAMP(S.SCHED_ACTV_START_DT_UTC), "US/Central")) AS Original_Schedule_StartTime_CST,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        DATETIME(TIMESTAMP(S.SCHED_ACTV_END_DT_UTC), "US/Central")) AS Original_Schedule_EndTime_CST,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        MIN(DATETIME(TIMESTAMP(S.SCHED_ACTV_START_TS_UTC), "US/Central"))) AS Schedule_StartTime_CST,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        MAX(DATETIME(TIMESTAMP(S.SCHED_ACTV_END_TS_UTC), "US/Central"))) AS Schedule_EndTime_CST,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        MIN(DATETIME(TIMESTAMP(S.SCHED_ACTV_START_TS_UTC), "Asia/Kolkata"))) AS Schedule_StartTime_IST,

    FORMAT_DATETIME('%Y-%m-%d %H:%M:%S',
        MAX(DATETIME(TIMESTAMP(S.SCHED_ACTV_END_TS_UTC), "Asia/Kolkata"))) AS Schedule_EndTime_IST,

    CONCAT(
        FORMAT_DATETIME('%m/%d/%Y',
            MIN(DATETIME(TIMESTAMP(S.SCHED_ACTV_START_DT_UTC), "US/Central"))),
        '-',
        S.AGNT_ACCT_ID
    ) AS Lookup_Reference,

    S.SCHED_ACTV_DUR_MIN_QTY  -- kept for Python-side deduplication (Open = longest duration)

FROM `wmt-cc-datasphere-prod.ces_prod_public.CS_AGNT_SCHED` S

LEFT OUTER JOIN AGNT_BEST A
    ON S.AGNT_ACCT_ID = A.VCC_AGNT_ID
    AND A._rn = 1   -- only the single best row per agent

WHERE S.SCHED_ACTV_START_DT_UTC BETWEEN '2025-11-01' AND CURRENT_DATE()
  AND S.SITE_NM IN (
      'WMT_IND_MAA_Digital_Support',
      'Fraud_IND_MAA',
      'Chargebacks_IND_MAA',
      'Fraud_Spvsr_IND_MAA',
      'Chargebacks_Spvsr_IND_MAA',
      'WMT_IND_MAA_Digital_Escal',
      'Transportation_IND_MAA',
      'Transportation_Spvsr_IND_MAA',
      'WMT_IND_MAA_Digital_Spvsr',
      'Account_Review_NST_WMT_IND_MAA',
      'Account_Review_WMT_IND_MAA',
      'WMT_IND_MAA_Digital_Chat',
      'Account_Review_SPV_WMT_IND_MAA',
      'WMT_IND_MAA_Digital_Chat_NST',
      'Transportation_Nest_IND_MAA',
      'Fraud Spvsr',
      'Pick Up/OLG',
      'Fraud',
      'Corp Gift Card',
      'Chargebacks Nest',
      'Corp Gift Card Spvsr',
      'Pick Up/OLG Spvsr',
      'Chargebacks',
      'Pick Up/OLG Nest',
      'Chargebacks Spvsr',
      'Fraud Nest',
      'TN',
      'Inactive Users',
      'WMT_IND_MAA_Account_Review',
      'WMT_IND_BLR_Account_Review',
      'WMT_IND_MAA_Account_Review_NST',
      'WMT_IND_BLR_Account_Review_NST',
      'WMT_IND_MAA_Account_Review_SPV',
      'WMT_IND_BLR_Account_Review_SPV',
      'WMT_IND_BLR_Digital_Chat',
      'WMT_IND_BLR_Digital_Chat_2',
      'WMT_IND_BLR_Digital_Chat_NST',
      'WMT_IND_BLR_Digital_Escal',
      'WMT_IND_BLR_Digital_Chat_SPV',
      'WMT_IND_BLR_Digital_Support',
      'WMT_IND_MAA_Chargebacks',
      'WMT_IND_MAA_Fraud',
      'WMT_IND_MAA_Fraud_NST',
      'WMT_IND_MAA_Fraud_SPV',
      'WMT_IND_MAA_Chargebacks_NST',
      'Account_Review_WMT_IND_BLR',
      'Account_Review_NST_WMT_IND_BLR',
      'Account_Review_SPV_WMT_IND_BLR',
      'WMT_IND_BLR_Chat',
      'WMT_IND_MAA_Digital_Chat_2',
      'WMT_IND_BLR_Chat_2',
      'WMT_IND_BLR_Chat_NST',
      'WMT_IND_BLR_Escal',
      'WMT_IND_BLR_Chat_SPV',
      'WMT_IND_BLR_Support',
      'WMT_IND_BLR_WMR_Voice',
      'WMT_IND_BLR_WMR_Voice_NST',
      'WMT_IND_BLR_WMR_Voice_Escal',
      'WMT_IND_BLR_WMR_Voice_SPV',
      'WMT_IND_BLR_Chargebacks',
      'WMT_IND_BLR_Chargebacks_NST',
      'WMT_IND_MAA_Chargebacks_SPV',
      'WMT_IND_BLR_Chargebacks_SPV',
      'Fraud_Nest_IND_MAA',
      'Chargebacks_Nest_IND_MAA',
      'WMT_IND_BLR_PERSONA',
      'WMT_IND_BLR_CR_VOICE',
      'WMT_IND_BLR_CR_VOICE_NST',
      'WMT_IND_BLR_CR_ESCAL',
      'WMT_IND_BLR_CR_SPV',
      'WMT_IND_BLR_DS_VOICE',
      'WMT_IND_BLR_DS_VOICE_NST',
      'WMT_IND_BLR_DS_ESCAL',
      'WMT_IND_BLR_DS_SPV',
      'WMT_IND_BLR_DAS_VOICE',
      'WMT_IND_BLR_DAS_VOICE_NST',
      'WMT_IND_BLR_DAS_ESCAL',
      'WMT_IND_BLR_DAS_SPV', 'null',
      'Corp GIFT CARD OB IND'
  )

GROUP BY
    S.SRC_APPLN_NM,
    S.AGNT_ACCT_ID,
    A.LOGIN_ID,
    A.WIN_NBR,
    A.AGNT_PROFL_NM,
    A.FIRST_NM,
    A.LAST_NM,
    A.EMAIL_ADDR_TXT,
    A.CNTCT_CHNL_NM,
    A.LVL1_MGR_LOGIN_ID,
    A.LVL1_MGR_LOGIN_NM,
    A.LVL2_MGR_LOGIN_ID,
    A.LVL2_MGR_LOGIN_NM,
    A.BUS_LINE_NM,
    A.BUS_SUB_LINE_NM,
    S.SITE_NM,
    S.GEO_REGION_CD,
    S.SCHED_ACTV_START_DT_UTC,
    S.SCHED_ACTV_END_DT_UTC,
    S.SCHED_ACTV_DUR_MIN_QTY
