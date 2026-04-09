```
=== Broker ===
[BROKER] Listening on redis://localhost:6379/0
[WORKER-2] Started. Monitoring 'default'...
[WORKER-1] Started. Monitoring 'default'...
[WORKER-3] Started. Monitoring 'default'...

=== Producer ===
Task queued: <Task id=f7232faa func=generate_thumbnail status=PENDING>
[WORKER-3] Picked up f7232faa (generate_thumbnail)
Task queued: <Task id=1bc46712 func=send_email status=PENDING>
[WORKER-2] Picked up 1bc46712 (send_email)
[WORKER-2] 1bc46712 FAILED (ConnectionError) - Retry 1 in 2s
Task queued: <Task id=04219227 func=generate_report status=PENDING>
[WORKER-1] Picked up 04219227 (generate_report)
[WORKER-1] 04219227 FAILED (ValueError) - Retry 1 in 2s
[WORKER-3] Completed f7232faa in 1.00s
[WORKER-3] Picked up 1bc46712 (send_email)
[WORKER-3] 1bc46712 FAILED (ConnectionError) - Retry 2 in 4s
[WORKER-2] Picked up 04219227 (generate_report)
[WORKER-2] 04219227 FAILED (ValueError) - Retry 2 in 4s
[WORKER-1] Picked up 1bc46712 (send_email)
[WORKER-3] Picked up 04219227 (generate_report)
[WORKER-1] Completed 1bc46712 in 0.00s
[WORKER-3] 04219227 moved to DLQ

=== Dashboard ===
Task ID    | Func       | Status       | Retries | Duration
------------------------------------------------------------
f7232faa   | generate_thumbnail | SUCCESS      | 0       | 1.00s
1bc46712   | send_email | SUCCESS      | 2       | 0.00s
3f3d0970   | generate_thumbnail | SUCCESS      | 0       | 1.00s
04219227   | generate_report | DEAD_LETTER  | 2       | —
5b302b0a   | generate_report | DEAD_LETTER  | 2       | —
c1a2a1ee   | send_email | SUCCESS      | 2       | 0.00s
```