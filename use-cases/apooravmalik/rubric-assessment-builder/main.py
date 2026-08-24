from __future__ import annotations

import argparse, html, json, os, time, uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

def load_local_env() -> None:
    path = Path(".env")
    if path.is_file():
        for line in path.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip())
load_local_env()

@dataclass
class Question: id:str; text:str; marks:int; question_type:str="short_answer"
@dataclass
class RubricRow: question_id:str; max_marks:int; full_credit:str; partial_credit:str; no_credit:str
@dataclass
class Package: title:str; topic:str; questions:list[Question]; rubric:list[RubricRow]

def build(topic:str,count:int,total_marks:int|None=None,grade:str|None=None)->Package:
    if not topic.strip() or count<1: raise ValueError("topic and a positive question count are required")
    if total_marks is not None and total_marks<count: raise ValueError("total marks must be at least question count")
    marks=[(total_marks or count)//count]*count
    for i in range((total_marks or count)%count): marks[i]+=1
    level=f"Grade {grade}" if grade else "the requested level"
    prompts=[
        f"Define a central concept in {topic} for {level}.",
        f"Explain how a key process in {topic} works, using one example.",
        f"Identify the main inputs and outputs involved in {topic}.",
        f"Compare two important ideas or stages in {topic}.",
        f"Apply {topic} to a new everyday or real-world scenario.",
    ]
    questions=[Question(f"Q{i+1}",prompts[i] if i<len(prompts) else f"Describe another important idea in {topic}, with an example (focus {i+1}).",marks[i]) for i in range(count)]
    rubric=[RubricRow(q.id,q.marks,f"Accurately explains {topic} with a relevant example.",f"Shows partial understanding of {topic}.","Missing, incorrect, or unrelated response.") for q in questions]
    package=Package(f"{topic} Assessment",topic,questions,rubric); validate(package,count,total_marks); return package

def validate(package:Package,requested:int|None=None,total:int|None=None)->None:
    ids=[q.id for q in package.questions]; rows=[r.question_id for r in package.rubric]
    if requested is not None and len(ids)!=requested: raise ValueError("question count mismatch")
    if len(ids)!=len(set(ids)): raise ValueError("duplicate question ID")
    if set(ids)!=set(rows) or len(rows)!=len(set(rows)): raise ValueError("question/rubric IDs are not one-to-one")
    marks={q.id:q.marks for q in package.questions}
    if any(marks[row.question_id]!=row.max_marks for row in package.rubric): raise ValueError("question/rubric marks mismatch")
    if total is not None and sum(marks.values())!=total: raise ValueError("total marks mismatch")

def render(package:Package)->str:
    questions="".join(f"<li data-question-id='{html.escape(q.id)}'><b>{html.escape(q.id)} ({q.marks} marks).</b> {html.escape(q.text)}</li>" for q in package.questions)
    rows="".join(f"<tr><td>{html.escape(r.question_id)}</td><td>{r.max_marks}</td><td>{html.escape(r.full_credit)}</td><td>{html.escape(r.partial_credit)}</td><td>{html.escape(r.no_credit)}</td></tr>" for r in package.rubric)
    return f"<h1>{html.escape(package.title)}</h1><h2>Assessment</h2><ol>{questions}</ol><h2>Rubric</h2><table><thead><tr><th>Question</th><th>Marks</th><th>Full credit</th><th>Partial credit</th><th>No credit</th></tr></thead><tbody>{rows}</tbody></table>"

class SuperDocs:
    def __init__(self,key:str,base:str=os.getenv("SUPERDOCS_BASE_URL","https://api.superdocs.app")):
        if not key: raise ValueError("SUPERDOCS_API_KEY is required")
        self.key,self.base=key,base.rstrip("/")
    def post(self,path:str,payload:dict):
        try:
            with urlopen(Request(self.base+path,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {self.key}","Content-Type":"application/json"},method="POST"),timeout=60) as r:
                raw=r.read(); return json.loads(raw) if r.headers.get_content_type()=="application/json" else raw
        except HTTPError as e: raise RuntimeError(f"SuperDocs HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    def create(self,html_document:str,title:str)->dict:
        return self.post("/v1/chat/async",{"session_id":"assessment-"+uuid.uuid4().hex,"message":"Create this exact assessment and rubric document. Preserve every question ID and mark.","document_html":html_document,"approval_mode":"approve_all"})
    def wait(self,job_id:str,max_polls:int=60)->dict:
        for _ in range(max_polls):
            try:
                with urlopen(Request(f"{self.base}/v1/jobs/{job_id}",headers={"Authorization":f"Bearer {self.key}"}),timeout=60) as response: state=json.loads(response.read())
            except HTTPError as error: raise RuntimeError(f"SuperDocs HTTP {error.code}") from error
            if state.get("status") not in {"pending","in_progress"}: return state
            time.sleep(1)
        raise RuntimeError("SuperDocs creation job did not reach a terminal state before polling limit")
    def export(self,session_id:str,path:str)->str:
        content=self.post("/v1/documents/export",{"session_id":session_id,"format":"docx"})
        if isinstance(content,dict):
            url=content.get("download_url") or content.get("url")
            if not url: raise RuntimeError("Export returned no artifact")
            with urlopen(url,timeout=60) as r: content=r.read()
        target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
        if not target.stat().st_size: raise RuntimeError("Export was empty")
        return str(target)

def publish(client,package:Package,auto:bool,output:str)->dict:
    validate(package); document=render(package)
    if not auto and input("Review the generated package above in JSON and create it in SuperDocs? [y/N] ").lower()!="y": return {"status":"REJECTED_BY_REVIEW","exported":False}
    result=client.create(document,package.title); session=result.get("session_id")
    if not session: return {"status":"CREATE_FAILED","error":"SuperDocs did not return session_id","exported":False}
    if not result.get("job_id"): return {"status":"CREATE_FAILED","error":"SuperDocs did not return job_id","exported":False}
    state=client.wait(result["job_id"])
    if state.get("status")!="completed": return {"status":"CREATE_FAILED","session_id":session,"error":f"SuperDocs job ended as {state.get('status','unknown')}","exported":False}
    try:return {"status":"COMPLETED","session_id":session,"export_path":client.export(session,output),"exported":True}
    except Exception as error:return {"status":"EXPORT_FAILED","session_id":session,"export_error":str(error),"exported":False}

if __name__=="__main__":
    p=argparse.ArgumentParser(description="Human-reviewed assessment and rubric builder")
    p.add_argument("--topic");p.add_argument("--grade");p.add_argument("--questions",type=int);p.add_argument("--total-marks",type=int);p.add_argument("--preview-only",action="store_true");p.add_argument("--auto-approve-demo",action="store_true");p.add_argument("--output",default="output/assessment-rubric.docx");a=p.parse_args()
    topic=a.topic or input("Assessment topic: ").strip(); questions=a.questions if a.questions is not None else int(input("Question count: ")); package=build(topic,questions,a.total_marks,a.grade)
    print(json.dumps({"package":asdict(package)},indent=2))
    if not a.preview_only: print(json.dumps({"result":publish(SuperDocs(os.getenv("SUPERDOCS_API_KEY","")),package,a.auto_approve_demo,a.output)},indent=2))
