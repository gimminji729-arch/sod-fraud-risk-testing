-- =====================================================================
-- Transaction-Level SoD & Fraud Risk Testing
-- Haneul Freight & Logistics (fictional) | Audit period: 2026-01-02 ~ 2026-03-31
-- Database: SQLite
-- Each test lists: rule, population, criteria, and expected use of results.
-- =====================================================================


-- ---------------------------------------------------------------------
-- T1. Status recorder approved own claim                        (R1)
-- Population: all claims
-- Exception : the person who recorded LOST/DAMAGED also approved the claim
-- ---------------------------------------------------------------------
SELECT c.claim_id,
       c.shipment_id,
       s.status        AS recorded_status,
       s.changed_by    AS recorded_by,
       c.approved_by,
       c.claim_amount,
       c.status        AS claim_status
FROM claims c
JOIN shipment_status_log s
  ON s.shipment_id = c.shipment_id
WHERE s.status IN ('LOST', 'DAMAGED')
  AND s.changed_by = c.approved_by
ORDER BY c.approved_by, c.claim_id;


-- ---------------------------------------------------------------------
-- T2. Claims clustered just below the approval limit            (R2)
-- Population: approved claims, non-manager approvers
-- Exception : amount between 90% and 100% of the limit in effect
--             at the time of approval (limit changes during the period)
-- ---------------------------------------------------------------------
SELECT c.claim_id,
       c.approved_by,
       e.job_title,
       c.claim_amount,
       h.value                                     AS limit_in_effect,
       ROUND(100.0 * c.claim_amount / h.value, 1)  AS pct_of_limit,
       c.approved_at
FROM claims c
JOIN employees e
  ON e.emp_id = c.approved_by
JOIN system_config_history h
  ON h.parameter = 'CLAIM_APPROVAL_LIMIT_NON_MANAGER'
 AND c.approved_at >= h.effective_from
 AND (h.effective_to IS NULL OR c.approved_at < h.effective_to)
WHERE e.system_role <> 'OPS_MANAGER'
  AND c.status = 'APPROVED'
  AND c.claim_amount BETWEEN 0.9 * h.value AND h.value
ORDER BY c.approved_by, c.approved_at;

-- T2 follow-up: share of each approver's approvals that sit near the limit
SELECT c.approved_by,
       COUNT(*) AS total_approved,
       SUM(CASE WHEN c.claim_amount BETWEEN 0.9 * h.value AND h.value
                THEN 1 ELSE 0 END) AS near_limit,
       ROUND(100.0 * SUM(CASE WHEN c.claim_amount BETWEEN 0.9 * h.value AND h.value
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS near_limit_pct
FROM claims c
JOIN employees e
  ON e.emp_id = c.approved_by
JOIN system_config_history h
  ON h.parameter = 'CLAIM_APPROVAL_LIMIT_NON_MANAGER'
 AND c.approved_at >= h.effective_from
 AND (h.effective_to IS NULL OR c.approved_at < h.effective_to)
WHERE e.system_role <> 'OPS_MANAGER'
  AND c.status = 'APPROVED'
GROUP BY c.approved_by;


-- ---------------------------------------------------------------------
-- T3. Duplicate claims                                          (R3)
-- Population: all claims
-- Exception : more than one claim on the same shipment
-- Note      : check status - a rejected duplicate means the control worked
-- ---------------------------------------------------------------------
SELECT shipment_id,
       COUNT(*)                   AS claim_count,
       GROUP_CONCAT(claim_id)     AS claim_ids,
       GROUP_CONCAT(status)       AS statuses,
       GROUP_CONCAT(approved_by)  AS approvers,
       SUM(paid_amount)           AS total_paid
FROM claims
GROUP BY shipment_id
HAVING COUNT(*) > 1;


-- ---------------------------------------------------------------------
-- T4. LOST claims with proof of delivery                        (R4)
-- Population: claims where claim_type = 'LOST'
-- Exception : a POD record exists for the shipment
-- ---------------------------------------------------------------------
SELECT c.claim_id,
       c.shipment_id,
       c.approved_by,
       c.claim_amount,
       p.delivered_at  AS pod_delivered_at,
       c.submitted_at  AS claim_submitted_at
FROM claims c
JOIN proof_of_delivery p
  ON p.shipment_id = c.shipment_id
WHERE c.claim_type = 'LOST'
ORDER BY c.claim_id;


-- ---------------------------------------------------------------------
-- T5. Self-closed exceptions                                    (R5)
-- Population: all exceptions
-- Exception : registered and closed by the same person within 24 hours
-- Risk level: LOST/DAMAGED = High (lead to payouts), others = Low
-- ---------------------------------------------------------------------
SELECT exception_id,
       shipment_id,
       exception_type,
       registered_by,
       registered_at,
       closed_at,
       ROUND((julianday(closed_at) - julianday(registered_at)) * 24, 1) AS hours_to_close,
       CASE WHEN exception_type IN ('LOST', 'DAMAGED') THEN 'High' ELSE 'Low' END AS risk_level
FROM exceptions
WHERE registered_by = closed_by
  AND (julianday(closed_at) - julianday(registered_at)) * 24 <= 24
ORDER BY risk_level, registered_by, exception_id;


-- ---------------------------------------------------------------------
-- T6. Inventory adjustment approval                             (R6)
-- Population: all inventory adjustments
-- Exception : (a) no approval, (b) self-approved, or
--             (c) value >= threshold but approver is not the Ops Manager
-- Threshold is read from system_config_history, not hard-coded
-- ---------------------------------------------------------------------
SELECT a.adj_id,
       a.sku_id,
       k.category,
       a.qty_change,
       ABS(a.qty_change) * k.unit_cost  AS adj_value,
       a.reason,
       a.adjusted_by,
       a.approved_by,
       CASE
         WHEN a.approved_by IS NULL          THEN 'No approval'
         WHEN a.approved_by = a.adjusted_by  THEN 'Self-approved'
         ELSE 'Approved below required authority'
       END AS exception_category
FROM inventory_adjustments a
JOIN skus k
  ON k.sku_id = a.sku_id
LEFT JOIN employees ap
  ON ap.emp_id = a.approved_by
WHERE a.approved_by IS NULL
   OR a.approved_by = a.adjusted_by
   OR (ABS(a.qty_change) * k.unit_cost >=
         (SELECT value FROM system_config_history
          WHERE parameter = 'INV_ADJ_MANAGER_APPROVAL_THRESHOLD'
            AND effective_to IS NULL)
       AND ap.system_role <> 'OPS_MANAGER')
ORDER BY exception_category, a.adj_id;


-- ---------------------------------------------------------------------
-- T7a. LOST/DAMAGED status changes outside business hours       (R7)
-- Population: status log entries with status LOST or DAMAGED
-- Exception : weekend, or before 08:00 / from 19:00 on weekdays
-- Limitation: public holidays are not considered (no holiday calendar)
-- ---------------------------------------------------------------------
SELECT log_id,
       shipment_id,
       status,
       changed_by,
       changed_at,
       CASE strftime('%w', changed_at)
         WHEN '0' THEN 'Sunday'
         WHEN '6' THEN 'Saturday'
         ELSE 'Weekday'
       END AS day_type
FROM shipment_status_log
WHERE status IN ('LOST', 'DAMAGED')
  AND (   strftime('%w', changed_at) IN ('0', '6')
       OR strftime('%H', changed_at) <  '08'
       OR strftime('%H', changed_at) >= '19')
ORDER BY changed_at;


-- ---------------------------------------------------------------------
-- T7b. DELIVERED status without proof of delivery               (R7)
-- Population: status log entries with status DELIVERED
-- Exception : no POD record, grouped by user and hour to detect bulk updates
-- ---------------------------------------------------------------------
SELECT s.changed_by,
       substr(s.changed_at, 1, 13) || ':00'  AS hour_bucket,
       COUNT(*)                              AS delivered_without_pod,
       MIN(s.changed_at)                     AS first_update,
       MAX(s.changed_at)                     AS last_update
FROM shipment_status_log s
LEFT JOIN proof_of_delivery p
  ON p.shipment_id = s.shipment_id
WHERE s.status = 'DELIVERED'
  AND p.pod_id IS NULL
GROUP BY s.changed_by, hour_bucket
ORDER BY delivered_without_pod DESC;


-- ---------------------------------------------------------------------
-- T8a. Configuration changes without an approved ticket         (R8)
-- ---------------------------------------------------------------------
SELECT h.*,
       e.job_title AS changed_by_title
FROM system_config_history h
JOIN employees e
  ON e.emp_id = h.changed_by
WHERE h.change_ticket IS NULL
   OR h.ticket_approved_by IS NULL;


-- ---------------------------------------------------------------------
-- T8b. Impact: claims approved above the authorized limit
--      while the unauthorized setting was active            (R2, R8)
-- Authorized limit: 500,000 KRW (CFG-001, approved ticket CHG-2024-118)
-- ---------------------------------------------------------------------
WITH unauthorized_window AS (
    SELECT effective_from,
           COALESCE(effective_to, '9999-12-31') AS effective_to
    FROM system_config_history
    WHERE parameter = 'CLAIM_APPROVAL_LIMIT_NON_MANAGER'
      AND change_ticket IS NULL
)
SELECT c.claim_id,
       c.approved_by,
       e.job_title,
       c.claim_type,
       c.claim_amount,
       c.approved_at
FROM claims c
JOIN employees e
  ON e.emp_id = c.approved_by
JOIN unauthorized_window u
  ON c.approved_at >= u.effective_from
 AND c.approved_at <  u.effective_to
WHERE e.system_role <> 'OPS_MANAGER'
  AND c.status = 'APPROVED'
  AND c.claim_amount > 500000
ORDER BY c.approved_at;


-- ---------------------------------------------------------------------
-- T9. Consolidated risk view: flags per employee
-- Combines T1, T2, T5, T7a
-- ---------------------------------------------------------------------
WITH
t1 AS (
    SELECT c.approved_by AS emp_id, COUNT(DISTINCT c.claim_id) AS n
    FROM claims c
    JOIN shipment_status_log s ON s.shipment_id = c.shipment_id
    WHERE s.status IN ('LOST', 'DAMAGED')
      AND s.changed_by = c.approved_by
    GROUP BY c.approved_by
),
t2 AS (
    SELECT c.approved_by AS emp_id, COUNT(*) AS n
    FROM claims c
    JOIN employees e ON e.emp_id = c.approved_by
    JOIN system_config_history h
      ON h.parameter = 'CLAIM_APPROVAL_LIMIT_NON_MANAGER'
     AND c.approved_at >= h.effective_from
     AND (h.effective_to IS NULL OR c.approved_at < h.effective_to)
    WHERE e.system_role <> 'OPS_MANAGER'
      AND c.status = 'APPROVED'
      AND c.claim_amount BETWEEN 0.9 * h.value AND h.value
    GROUP BY c.approved_by
),
t5 AS (
    SELECT registered_by AS emp_id, COUNT(*) AS n
    FROM exceptions
    WHERE registered_by = closed_by
      AND (julianday(closed_at) - julianday(registered_at)) * 24 <= 24
    GROUP BY registered_by
),
t7 AS (
    SELECT changed_by AS emp_id, COUNT(*) AS n
    FROM shipment_status_log
    WHERE status IN ('LOST', 'DAMAGED')
      AND (   strftime('%w', changed_at) IN ('0', '6')
           OR strftime('%H', changed_at) <  '08'
           OR strftime('%H', changed_at) >= '19')
    GROUP BY changed_by
),
summary AS (
    SELECT e.emp_id,
           e.name,
           e.job_title,
           COALESCE(t1.n, 0) AS t1_sod_conflict,
           COALESCE(t2.n, 0) AS t2_near_limit,
           COALESCE(t5.n, 0) AS t5_self_closed,
           COALESCE(t7.n, 0) AS t7_after_hours
    FROM employees e
    LEFT JOIN t1 ON t1.emp_id = e.emp_id
    LEFT JOIN t2 ON t2.emp_id = e.emp_id
    LEFT JOIN t5 ON t5.emp_id = e.emp_id
    LEFT JOIN t7 ON t7.emp_id = e.emp_id
)
SELECT *,
       t1_sod_conflict + t2_near_limit + t5_self_closed + t7_after_hours AS total_flags
FROM summary
WHERE t1_sod_conflict + t2_near_limit + t5_self_closed + t7_after_hours > 0
ORDER BY total_flags DESC;


-- ---------------------------------------------------------------------
-- T10. Additional analysis: customer concentration of T1 claims
-- Who onboarded the customers that received the flagged payouts?
-- ---------------------------------------------------------------------
SELECT cu.customer_id,
       cu.customer_name,
       cu.onboarded_by,
       cu.onboarded_at,
       COUNT(DISTINCT c.claim_id)  AS flagged_claims,
       SUM(c.claim_amount)         AS flagged_amount
FROM claims c
JOIN shipment_status_log s
  ON s.shipment_id = c.shipment_id
JOIN customers cu
  ON cu.customer_id = c.customer_id
WHERE s.status IN ('LOST', 'DAMAGED')
  AND s.changed_by = c.approved_by
GROUP BY cu.customer_id, cu.customer_name, cu.onboarded_by, cu.onboarded_at
ORDER BY flagged_claims DESC;
