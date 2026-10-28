"""Focused regression checks for the smoothing algorithm and validation limits."""
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'site'))
from smoothllm import defend, perturb
from safety import validate_messages, ValidationError, SYSTEM_PROMPT

original=[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':'Summarise the fictional news article.'}]
assert perturb(original[-1]['content'],random.Random(4)) == perturb(original[-1]['content'],random.Random(4))
assert len(perturb('a'*100,random.Random(4))) == 110
seen=[]
answers=iter(['I cannot assist.','I cannot provide that.','I am unable to help.','Test answer.','Another answer.'])
def fake(model,messages,**kwargs):
    seen.append(messages)
    return {'message':{'content':next(answers)}}
response,vote,_=defend('test',original,seed=4,call=fake)
assert vote['refusal_votes']==3 and vote['selected_refusal']
assert original[-1]['content']=='Summarise the fictional news article.'
assert all(m[0]==original[0] for m in seen)
for bad in [4001,5000]:
    try: validate_messages({'messages':[{'role':'user','content':'x'*bad}]})
    except ValidationError as e: assert e.status==413
    else: raise AssertionError('size accepted')
assert len(validate_messages({'messages':[{'role':'user','content':'x'*4000}]}))==2
history=[{'role':'user','content':str(i)} for i in range(20)]
assert len(validate_messages({'messages':history}))==13
try: validate_messages({'messages':[{'role':'system','content':'test'}]+history})
except ValidationError as e: assert e.code=='untrusted_role'
else: raise AssertionError('role accepted before history truncation')
print('PASS: reproducibility, perturbation size, majority selection, unchanged input/system, limits and full-history validation')
