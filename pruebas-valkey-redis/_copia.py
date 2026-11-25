import redis, time; o=redis.Redis(host='redis'); d=redis.Redis(host='valkey'); p=o.pipeline(); [p.set(f'c:{i}', 'x'*50) for i in range(100000)]; p.execute(); o.set('una','hola'); 
try:
 d.restore('una', 0, o.dump('una')); print('DUMP/RESTORE: OK')
except Exception as e:
 print('DUMP/RESTORE:', type(e).__name__, e)
t=time.perf_counter(); n=0
cur=0
while True:
 cur, ks = o.scan(cur, count=1000)
 if ks:
  vs=o.mget(ks); q=d.pipeline(); [q.set(k,v) for k,v in zip(ks,vs) if v is not None]; q.execute(); n+=len(ks)
 if cur==0: break
print(f'copia lógica SCAN+MGET+SET: {n} claves en {time.perf_counter()-t:.2f} s'); print('DBSIZE en valkey:', d.dbsize())