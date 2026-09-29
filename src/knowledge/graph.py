"""Evidence-grounded SQLite knowledge graph with enforced provenance registry."""
from __future__ import annotations

import hashlib, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import DATA_DIR
from src.evidence.identity import ids_for_record
from src.evidence.integrity import validate_raw_record


class KnowledgeGraph:
    DEFAULT_DB_PATH=DATA_DIR/"knowledge"/"abangcolek_v4.db"
    def __init__(self,db_path:Optional[Union[str,Path]]=None):
        self.db_path=Path(db_path or self.DEFAULT_DB_PATH); self.db_path.parent.mkdir(parents=True,exist_ok=True)
        self.conn=sqlite3.connect(str(self.db_path),check_same_thread=False); self.conn.row_factory=sqlite3.Row; self.conn.execute("PRAGMA foreign_keys=ON"); self.init_schema()
    def close(self): self.conn.close()
    def init_schema(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS graph_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS evidence_registry(capture_id TEXT PRIMARY KEY,content_id TEXT NOT NULL,platform TEXT NOT NULL,native_id TEXT,raw_hash TEXT NOT NULL UNIQUE,source_url TEXT,record_kind TEXT,created_at TEXT NOT NULL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS entities(entity_id TEXT PRIMARY KEY,entity_type TEXT NOT NULL,name TEXT NOT NULL,canonical_name TEXT,trust_score REAL,metadata_json TEXT,created_at TEXT NOT NULL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS relationships(rel_id TEXT PRIMARY KEY,source_id TEXT NOT NULL,target_id TEXT NOT NULL,relation_type TEXT NOT NULL,confidence REAL,epistemology_class TEXT NOT NULL,first_seen TEXT,last_seen TEXT,FOREIGN KEY(source_id) REFERENCES entities(entity_id),FOREIGN KEY(target_id) REFERENCES entities(entity_id))")
            self.conn.execute("CREATE TABLE IF NOT EXISTS relationship_evidence(rel_id TEXT NOT NULL,capture_id TEXT NOT NULL,PRIMARY KEY(rel_id,capture_id),FOREIGN KEY(rel_id) REFERENCES relationships(rel_id) ON DELETE CASCADE,FOREIGN KEY(capture_id) REFERENCES evidence_registry(capture_id))")
            self.conn.execute("CREATE TABLE IF NOT EXISTS epistemology(item_id TEXT PRIMARY KEY,item_type TEXT NOT NULL,statement TEXT NOT NULL,confidence REAL,status TEXT NOT NULL,created_at TEXT NOT NULL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS epistemology_evidence(item_id TEXT NOT NULL,capture_id TEXT NOT NULL,PRIMARY KEY(item_id,capture_id),FOREIGN KEY(item_id) REFERENCES epistemology(item_id) ON DELETE CASCADE,FOREIGN KEY(capture_id) REFERENCES evidence_registry(capture_id))")
            self.conn.execute("CREATE TABLE IF NOT EXISTS timeline_events(event_id TEXT PRIMARY KEY,event_date TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,entity_ids_json TEXT NOT NULL,confidence REAL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS timeline_evidence(event_id TEXT NOT NULL,capture_id TEXT NOT NULL,PRIMARY KEY(event_id,capture_id),FOREIGN KEY(event_id) REFERENCES timeline_events(event_id) ON DELETE CASCADE,FOREIGN KEY(capture_id) REFERENCES evidence_registry(capture_id))")
    def clear(self):
        with self.conn:
            for table in ("relationship_evidence","epistemology_evidence","timeline_evidence","relationships","epistemology","timeline_events","entities","evidence_registry","graph_metadata"): self.conn.execute(f"DELETE FROM {table}")
    def register_evidence(self,record:Dict[str,Any]):
        validate_raw_record(record,require_authoritative=True); ids=record.get("_ids") or ids_for_record(record); now=datetime.now(timezone.utc).isoformat()
        with self.conn: self.conn.execute("INSERT OR REPLACE INTO evidence_registry VALUES(?,?,?,?,?,?,?,?)",(ids["capture_id"],ids["content_id"],record.get("source_platform","unknown"),record.get("source_native_id"),record.get("raw_hash"),record.get("source_url"),ids["record_kind"],now))
        return ids
    def _evidence_exists(self,capture_id:str)->bool: return self.conn.execute("SELECT 1 FROM evidence_registry WHERE capture_id=?",(capture_id,)).fetchone() is not None
    def _require_evidence(self,evidence_ids:List[str]):
        if not evidence_ids: raise ValueError("Evidence IDs are required")
        missing=[x for x in evidence_ids if not self._evidence_exists(x)]
        if missing: raise ValueError(f"Unknown/orphan evidence IDs: {missing}")

    def add_entity(self,entity_id:str,entity_type:str,name:str,canonical_name:Optional[str]=None,trust_score:Optional[float]=None,metadata:Optional[Dict[str,Any]]=None):
        now=datetime.now(timezone.utc).isoformat(); meta=metadata or {}
        with self.conn: self.conn.execute("INSERT INTO entities VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET entity_type=excluded.entity_type,name=excluded.name,canonical_name=excluded.canonical_name,trust_score=excluded.trust_score,metadata_json=excluded.metadata_json",(entity_id,entity_type,name,canonical_name or name,trust_score,json.dumps(meta,ensure_ascii=False),now))
        return {"entity_id":entity_id,"entity_type":entity_type,"name":name,"canonical_name":canonical_name or name,"trust_score":trust_score,"metadata":meta,"created_at":now}
    def get_entity(self,identifier:str):
        r=self.conn.execute("SELECT * FROM entities WHERE entity_id=? OR name=? LIMIT 1",(identifier,identifier)).fetchone()
        if not r:return None
        return {"entity_id":r["entity_id"],"entity_type":r["entity_type"],"name":r["name"],"canonical_name":r["canonical_name"],"trust_score":r["trust_score"],"metadata":json.loads(r["metadata_json"] or "{}"),"created_at":r["created_at"]}
    def get_entities_by_type(self,entity_type:str): return [self.get_entity(r[0]) for r in self.conn.execute("SELECT entity_id FROM entities WHERE LOWER(entity_type)=LOWER(?)",(entity_type,)).fetchall()]
    @staticmethod
    def _stable_id(prefix:str,*parts)->str: return f"{prefix}_{hashlib.sha256('|'.join(str(x) for x in parts).encode()).hexdigest()[:24]}"
    def add_relationship(self,source_id:str,target_id:str,relation_type:str,evidence_ids:List[str],confidence:Optional[float]=None,epistemology_class:str="OBSERVED_FACT",first_seen:Optional[str]=None,last_seen:Optional[str]=None):
        self._require_evidence(evidence_ids)
        if not self.get_entity(source_id) or not self.get_entity(target_id): raise ValueError("Relationship endpoints must exist")
        rid=self._stable_id("rel",source_id,target_id,relation_type,*sorted(evidence_ids))
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO relationships VALUES(?,?,?,?,?,?,?,?)",(rid,source_id,target_id,relation_type,confidence,epistemology_class,first_seen,last_seen))
            for eid in sorted(set(evidence_ids)): self.conn.execute("INSERT OR IGNORE INTO relationship_evidence VALUES(?,?)",(rid,eid))
        return {"rel_id":rid,"source_id":source_id,"target_id":target_id,"relation_type":relation_type,"evidence_ids":evidence_ids,"confidence":confidence,"epistemology_class":epistemology_class}
    def add_epistemology_item(self,statement:str,item_type:str="INFERENCE",evidence_ids:Optional[List[str]]=None,confidence:Optional[float]=None,status:str="SUPPORTED",item_id:Optional[str]=None):
        ev=evidence_ids or []; kind=item_type.upper(); self._require_evidence(ev)
        if kind=="HYPOTHESIS" and status=="VERIFIED": raise ValueError("Hypothesis cannot be directly VERIFIED")
        iid=item_id or self._stable_id("epis",kind,statement,*sorted(ev)); now=datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO epistemology VALUES(?,?,?,?,?,?)",(iid,kind,statement,confidence,status,now))
            for eid in sorted(set(ev)): self.conn.execute("INSERT OR IGNORE INTO epistemology_evidence VALUES(?,?)",(iid,eid))
        return {"item_id":iid,"item_type":kind,"statement":statement,"evidence_ids":ev,"confidence":confidence,"status":status,"created_at":now}
    def add_timeline_event(self,event_id:Optional[str]=None,event_date:str="",title:str="",description:str="",entity_ids:Optional[List[str]]=None,evidence_ids:Optional[List[str]]=None,confidence:Optional[float]=None):
        ev=evidence_ids or []; self._require_evidence(ev); eid=event_id or self._stable_id("evt",event_date,title,*sorted(ev)); ents=entity_ids or []
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO timeline_events VALUES(?,?,?,?,?,?)",(eid,event_date,title,description,json.dumps(ents),confidence))
            for cap in sorted(set(ev)): self.conn.execute("INSERT OR IGNORE INTO timeline_evidence VALUES(?,?)",(eid,cap))
        return {"event_id":eid,"event_date":event_date,"title":title,"description":description,"entity_ids":ents,"evidence_ids":ev,"confidence":confidence}

    def get_epistemology_items(self,item_type:Optional[str]=None):
        q="SELECT * FROM epistemology"+(" WHERE LOWER(item_type)=LOWER(?)" if item_type else ""); rows=self.conn.execute(q,(item_type,) if item_type else ()).fetchall(); out=[]
        for r in rows:
            ev=[x[0] for x in self.conn.execute("SELECT capture_id FROM epistemology_evidence WHERE item_id=?",(r["item_id"],)).fetchall()]
            out.append({"item_id":r["item_id"],"item_type":r["item_type"],"statement":r["statement"],"evidence_ids":ev,"confidence":r["confidence"],"status":r["status"],"created_at":r["created_at"]})
        return out
    def get_timeline(self,ascending:bool=True):
        rows=self.conn.execute(f"SELECT * FROM timeline_events ORDER BY event_date {'ASC' if ascending else 'DESC'}").fetchall(); out=[]
        for r in rows:
            ev=[x[0] for x in self.conn.execute("SELECT capture_id FROM timeline_evidence WHERE event_id=?",(r["event_id"],)).fetchall()]
            out.append({"event_id":r["event_id"],"event_date":r["event_date"],"title":r["title"],"description":r["description"],"entity_ids":json.loads(r["entity_ids_json"] or "[]"),"evidence_ids":ev,"confidence":r["confidence"]})
        return out
    def get_entity_neighborhood(self,entity_id:str):
        ent=self.get_entity(entity_id)
        if not ent:return {"entity":None,"outgoing":[],"incoming":[],"neighbors":[]}
        outs=self.conn.execute("SELECT * FROM relationships WHERE source_id=?",(entity_id,)).fetchall(); ins=self.conn.execute("SELECT * FROM relationships WHERE target_id=?",(entity_id,)).fetchall()
        def pack(r,target=True):
            ev=[x[0] for x in self.conn.execute("SELECT capture_id FROM relationship_evidence WHERE rel_id=?",(r["rel_id"],)).fetchall()]
            return {"rel_id":r["rel_id"],("target_id" if target else "source_id"):r["target_id"] if target else r["source_id"],"relation_type":r["relation_type"],"evidence_ids":ev,"confidence":r["confidence"]}
        outgoing=[pack(r,True) for r in outs]; incoming=[pack(r,False) for r in ins]; ids={x["target_id"] for x in outgoing}|{x["source_id"] for x in incoming}
        return {"entity":ent,"outgoing":outgoing,"incoming":incoming,"neighbors":[self.get_entity(x) for x in ids if self.get_entity(x)]}
    def query_provenance(self,evidence_id:str):
        rel=[r[0] for r in self.conn.execute("SELECT rel_id FROM relationship_evidence WHERE capture_id=?",(evidence_id,)).fetchall()]
        epi=[r[0] for r in self.conn.execute("SELECT item_id FROM epistemology_evidence WHERE capture_id=?",(evidence_id,)).fetchall()]
        evt=[r[0] for r in self.conn.execute("SELECT event_id FROM timeline_evidence WHERE capture_id=?",(evidence_id,)).fetchall()]
        return {"evidence_id":evidence_id,"total_references":len(rel)+len(epi)+len(evt),"relationship_ids":rel,"epistemology_item_ids":epi,"timeline_event_ids":evt}
    def populate_foundational_records(self): raise RuntimeError("Hard-coded foundational business records are disabled")

    def build_from_verified_evidence(self,raw_records:Optional[List[Dict[str,Any]]]=None,raw_dir:Union[str,Path]="",decisions_file:Union[str,Path]="",run_id:Optional[str]=None,input_fingerprint:Optional[str]=None):
        # Backward-compatible positional form: build_from_verified_evidence(raw_dir, decisions_file)
        if isinstance(raw_records,(str,Path)):
            legacy_raw=raw_records; legacy_decisions=raw_dir
            raw_records=None; raw_dir=legacy_raw; decisions_file=legacy_decisions
        self.clear()
        with self.conn:
            if run_id: self.conn.execute("INSERT OR REPLACE INTO graph_metadata VALUES(?,?)",("run_id",str(run_id)))
            if input_fingerprint: self.conn.execute("INSERT OR REPLACE INTO graph_metadata VALUES(?,?)",("input_fingerprint",str(input_fingerprint)))
        if raw_records is None:
            from src.jev.batch_runner import JevBatchRunner
            raw_records=JevBatchRunner(raw_dir=Path(raw_dir) if raw_dir else None).load_raw_sources()
        by_capture={}
        for rec in raw_records:
            ids=self.register_evidence(rec); by_capture[ids["capture_id"]]=rec; ev_ent=f"evidence:{ids['content_id']}"; platform=rec.get("source_platform","unknown"); plat=f"platform:{platform}"
            self.add_entity(ev_ent,"EVIDENCE",ids["content_id"],metadata={"native_id":rec.get("source_native_id"),"raw_hash":rec.get("raw_hash"),"source_url":rec.get("source_url"),"record_kind":ids["record_kind"]})
            self.add_entity(plat,"PLATFORM",platform)
            self.add_relationship(ev_ent,plat,"OBSERVED_ON",[ids["capture_id"]],confidence=None,epistemology_class="OBSERVED_FACT",first_seen=rec.get("published_at") or rec.get("captured_at"))
            if rec.get("published_at"): self.add_timeline_event(event_id=self._stable_id("evt",ids["content_id"]),event_date=str(rec["published_at"]),title=f"Observed {ids['record_kind']}",description="Source record observed",entity_ids=[ev_ent,plat],evidence_ids=[ids["capture_id"]],confidence=None)
        dp=Path(decisions_file) if decisions_file else None
        if dp and dp.exists():
            data=json.loads(dp.read_text(encoding="utf-8"))
            for d in data.get("decisions",[]):
                cap=d.get("capture_id") or d.get("source_evidence_id")
                if d.get("authoritative") is not True or d.get("decision_engine")!="TYPESAFE_JEV" or cap not in by_capture: continue
                self.add_epistemology_item(statement=f"JEV {d.get('evaluation_type')} classification: {json.dumps(d.get('classified',{}),sort_keys=True)}",item_type="CLASSIFICATION",evidence_ids=[cap],confidence=d.get("confidence"),status="SUPPORTED",item_id=d.get("decision_id"))
        return self.get_summary()
    def get_summary(self):
        names=("evidence_registry","entities","relationships","epistemology","timeline_events"); counts={name:self.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in names}
        meta={r[0]:r[1] for r in self.conn.execute("SELECT key,value FROM graph_metadata").fetchall()}
        return {"db_path":str(self.db_path),"run_id":meta.get("run_id"),"input_fingerprint":meta.get("input_fingerprint"),"total_evidence":counts["evidence_registry"],"total_entities":counts["entities"],"total_relationships":counts["relationships"],"total_epistemology_items":counts["epistemology"],"total_timeline_events":counts["timeline_events"]}


KnowledgeGraphV2=KnowledgeGraph
if __name__=="__main__":
    kg=KnowledgeGraph(); print(json.dumps(kg.build_from_verified_evidence(),indent=2)); kg.close()
