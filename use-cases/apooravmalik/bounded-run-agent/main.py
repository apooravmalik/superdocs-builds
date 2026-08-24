from __future__ import annotations

import argparse, json, mimetypes, os, re, time, uuid
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

def load_local_env() -> None:
    path = Path(".env")
    if path.is_file():
        for line in path.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip())
load_local_env()

class TaskStatus(StrEnum): PENDING="PENDING"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; FAILED="FAILED"; NOT_ATTEMPTED="NOT_ATTEMPTED"
class RunStatus(StrEnum): COMPLETED="COMPLETED"; PARTIALLY_COMPLETED="PARTIALLY_COMPLETED"; FAILED="FAILED"; BUDGET_EXHAUSTED="BUDGET_EXHAUSTED"; DEADLINE_EXCEEDED="DEADLINE_EXCEEDED"
@dataclass
class Task: id:str; description:str; status:TaskStatus=TaskStatus.PENDING; error:str|None=None

def plan(request:str)->list[Task]:
    pieces=[re.sub(r"^\d+[.)]\s*","",x.strip()) for x in re.split(r";|\n",request) if x.strip()]
    if not pieces: raise ValueError("Request needs at least one task")
    return [Task(f"T{i}",text) for i,text in enumerate(pieces[:20],1)]

class SuperDocs:
    def __init__(self,key:str,base:str=os.getenv("SUPERDOCS_BASE_URL","https://api.superdocs.app")):
        if not key: raise ValueError("SUPERDOCS_API_KEY is required")
        self.key,self.base=key,base.rstrip("/")
    def request(self,path:str,payload:dict|None=None,body:bytes|None=None,ctype="application/json"):
        headers={"Authorization":f"Bearer {self.key}","Accept":"application/json"}
        body=json.dumps(payload or {}).encode() if body is None else body
        if ctype: headers["Content-Type"]=ctype
        try:
            with urlopen(Request(self.base+path,data=body,headers=headers,method="POST"),timeout=60) as r:
                raw=r.read(); return json.loads(raw) if r.headers.get_content_type()=="application/json" else raw
        except HTTPError as e: raise RuntimeError(f"SuperDocs HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
        except URLError as e: raise RuntimeError(f"SuperDocs network error: {e.reason}") from e
    def upload(self,file_path:str,session_id:str)->dict:
        path=Path(file_path); boundary="----run"+uuid.uuid4().hex
        if not path.is_file(): raise FileNotFoundError(path)
        mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body=b"\r\n".join([f"--{boundary}".encode(),b'Content-Disposition: form-data; name="session_id"',b"",session_id.encode(),f"--{boundary}".encode(),f'Content-Disposition: form-data; name="file"; filename="{path.name}"'.encode(),f"Content-Type: {mime}".encode(),b"",path.read_bytes(),f"--{boundary}--".encode(),b""])
        return self.request("/v1/documents/upload?index=true",body=body,ctype=f"multipart/form-data; boundary={boundary}")
    def edit(self,session:str,instruction:str)->dict: return self.request("/v1/chat/async",{"session_id":session,"message":instruction,"approval_mode":"ask_every_time","response_mode":"compact"})
    def job(self,job_id:str)->dict:
        try:
            with urlopen(Request(f"{self.base}/v1/jobs/{job_id}",headers={"Authorization":f"Bearer {self.key}"}),timeout=60) as r:return json.loads(r.read())
        except HTTPError as e: raise RuntimeError(f"SuperDocs HTTP {e.code}") from e
    def approve(self,session:str,job_id:str,changes:list[dict])->dict:return self.request(f"/v1/chat/{session}/approve",{"job_id":job_id,"approved":True,"changes":changes})
    def wait(self,job_id:str,max_polls:int=60)->dict:
        for _ in range(max_polls):
            state=self.job(job_id)
            if state.get("status") not in {"pending","in_progress"}: return state
            time.sleep(1)
        raise RuntimeError("SuperDocs job did not reach a terminal state before polling limit")
    def export(self,session:str,path:str)->str:
        result=self.request("/v1/documents/export",{"session_id":session,"format":"docx"})
        if isinstance(result,dict):
            url=result.get("download_url") or result.get("url")
            if not url: raise RuntimeError("Export returned no artifact")
            with urlopen(url,timeout=60) as r: result=r.read()
        target=Path(path); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(result)
        if not target.stat().st_size: raise RuntimeError("Export was empty")
        return str(target)

def run(client, file_path:str, request:str, max_operations:int, deadline:float|None, auto:bool, output:str, clock=time.monotonic)->dict:
    if max_operations<1: raise ValueError("max_operations must be at least 1")
    tasks,started,used,stop=plan(request),clock(),0,None; session="run-"+uuid.uuid4().hex
    client.upload(file_path,session)
    for task in tasks:
        if used>=max_operations: stop="OPERATION_BUDGET_EXHAUSTED"; break
        if deadline is not None and clock()-started>=deadline: stop="DEADLINE_EXCEEDED"; break
        task.status=TaskStatus.IN_PROGRESS
        try:
            job=client.edit(session,task.description); used+=1; state=client.wait(job["job_id"])
            if state.get("status")=="awaiting_approval":
                approved=auto or input(f"Approve {task.id}: {task.description}? [y/N] ").lower()=="y"
                if not approved: task.status,task.error,stop=TaskStatus.FAILED,"Approval rejected","APPROVAL_REJECTED"; break
                changes=(state.get("metadata") or {}).get("pending_changes") or []
                client.approve(session,job["job_id"],[{"change_id":c["change_id"],"approved":True} for c in changes]); state=client.wait(job["job_id"])
            if state.get("status")=="completed": task.status=TaskStatus.COMPLETED
            else: task.status,task.error=TaskStatus.FAILED,f"Job ended as {state.get('status','unknown')}"
        except Exception as e: task.status,task.error=TaskStatus.FAILED,str(e)
    if stop:
        for task in tasks:
            if task.status==TaskStatus.PENDING: task.status=TaskStatus.NOT_ATTEMPTED
    completed=sum(x.status==TaskStatus.COMPLETED for x in tasks)
    status=RunStatus.BUDGET_EXHAUSTED if stop=="OPERATION_BUDGET_EXHAUSTED" else RunStatus.DEADLINE_EXCEEDED if stop=="DEADLINE_EXCEEDED" else RunStatus.COMPLETED if completed==len(tasks) else RunStatus.PARTIALLY_COMPLETED if completed else RunStatus.FAILED
    result={"status":status,"stop_reason":stop,"operations_used":used,"operations_allowed":max_operations,"elapsed_seconds":round(clock()-started,3),"completed":[x.id for x in tasks if x.status==TaskStatus.COMPLETED],"failed":[asdict(x) for x in tasks if x.status==TaskStatus.FAILED],"not_completed":[x.id for x in tasks if x.status!=TaskStatus.COMPLETED],"tasks":[asdict(x) for x in tasks]}
    try: result["export_path"]=client.export(session,output)
    except Exception as e: result["export_error"]=str(e)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--file",required=True);p.add_argument("--request",required=True);p.add_argument("--max-operations",type=int,required=True);p.add_argument("--deadline-seconds",type=float);p.add_argument("--auto-approve-demo",action="store_true");p.add_argument("--output",default="output/result.docx");a=p.parse_args()
    print(json.dumps(run(SuperDocs(os.getenv("SUPERDOCS_API_KEY","")),a.file,a.request,a.max_operations,a.deadline_seconds,a.auto_approve_demo,a.output),indent=2,default=str))
