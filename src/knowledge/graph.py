"""Evidence-grounded SQLite knowledge graph. No seeded business facts."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from src.evidence.integrity import validate_raw_record

class KnowledgeGraph:
    DEFAULT_DB_PATH=Path('D:/ABANGCOLEK/data/knowledge/abangcolek_v3.db')
    def __init__(self,db_path:Optional[Union[str,Path]]=None):
        self.db_path=Path(db_path or self.DEFAULT_DB_PATH); self.db_path.parent.mkdir(parents=True,exist_ok=True)
        self.conn=sqlite3.connect(str(self.db_path),check_same_thread=False); self.conn.row_factory=sqlite3.Row; self.conn.execute('PRAGMA foreign_keys=ON'); self.init_schema()
    def close(self):
        if self.conn: self.conn.close()
    def init_schema(self):
        with self.conn:
            self.conn.execute('CREATE TABLE IF NOT EXISTS entities(entity_id TEXT PRIMARY KEY,entity_type TEXT NOT NULL,name TEXT NOT NULL,canonical_name TEXT,trust_score REAL DEFAULT 1.0,metadata_json TEXT,created_at TEXT NOT NULL)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS relationships(rel_id TEXT PRIMARY KEY,source_id TEXT NOT NULL,target_id TEXT NOT NULL,relation_type TEXT NOT NULL,evidence_ids_json TEXT NOT NULL,confidence REAL DEFAULT 1.0,epistemology_class TEXT DEFAULT "OBSERVED_FACT",first_seen TEXT,last_seen TEXT,FOREIGN KEY(source_id) REFERENCES entities(entity_id),FOREIGN KEY(target_id) REFERENCES entities(entity_id))')
            self.conn.execute('CREATE TABLE IF NOT EXISTS epistemology(item_id TEXT PRIMARY KEY,item_type TEXT NOT NULL,statement TEXT NOT NULL,evidence_ids_json TEXT NOT NULL,confidence REAL DEFAULT 1.0,status TEXT NOT NULL,created_at TEXT NOT NULL)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS timeline_events(event_id TEXT PRIMARY KEY,event_date TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,entity_ids_json TEXT NOT NULL,evidence_ids_json TEXT NOT NULL,confidence REAL DEFAULT 1.0)')
    def clear(self):
        with self.conn:
            for t in ('relationships','epistemology','timeline_events','entities'): self.conn.execute(f'DELETE FROM {t}')
    def add_entity(self,entity_id:str,entity_type:str,name:str,canonical_name:Optional[str]=None,trust_score:float=1.0,metadata:Optional[Dict[str,Any]]=None):
        now=datetime.now(timezone.utc).isoformat(); meta=metadata or {}
        with self.conn: self.conn.execute('INSERT INTO entities VALUES(?,?,?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET entity_type=excluded.entity_type,name=excluded.name,canonical_name=excluded.canonical_name,trust_score=excluded.trust_score,metadata_json=excluded.metadata_json',(entity_id,entity_type,name,canonical_name or name,trust_score,json.dumps(meta,ensure_ascii=False),now))
        return {'entity_id':entity_id,'entity_type':entity_type,'name':name,'canonical_name':canonical_name or name,'trust_score':trust_score,'metadata':meta,'created_at':now}
    def get_entity(self,identifier:str):
        row=self.conn.execute('SELECT * FROM entities WHERE entity_id=? OR name=? LIMIT 1',(identifier,identifier)).fetchone()
        if not row: return None
        return {'entity_id':row['entity_id'],'entity_type':row['entity_type'],'name':row['name'],'canonical_name':row['canonical_name'],'trust_score':row['trust_score'],'metadata':json.loads(row['metadata_json'] or '{}'),'created_at':row['created_at']}
    def get_entities_by_type(self,entity_type:str):
        rows=self.conn.execute('SELECT * FROM entities WHERE LOWER(entity_type)=LOWER(?)',(entity_type,)).fetchall()
        return [self.get_entity(r['entity_id']) for r in rows]
    def add_relationship(self,source_id:str,target_id:str,relation_type:str,evidence_ids:List[str],confidence:float=1.0,epistemology_class:str='OBSERVED_FACT',first_seen:Optional[str]=None,last_seen:Optional[str]=None):
        if not evidence_ids: raise ValueError('Relationship requires evidence_ids')
        if not self.get_entity(source_id) or not self.get_entity(target_id): raise ValueError('Relationship endpoints must exist')
        rid=f'rel_{uuid4().hex[:12]}'
        with self.conn: self.conn.execute('INSERT INTO relationships VALUES(?,?,?,?,?,?,?,?,?)',(rid,source_id,target_id,relation_type,json.dumps(evidence_ids),confidence,epistemology_class,first_seen,last_seen))
        return {'rel_id':rid,'source_id':source_id,'target_id':target_id,'relation_type':relation_type,'evidence_ids':evidence_ids,'confidence':confidence,'epistemology_class':epistemology_class,'first_seen':first_seen,'last_seen':last_seen}
    def add_epistemology_item(self,statement:str,item_type:str='INFERENCE',evidence_ids:Optional[List[str]]=None,confidence:float=1.0,status:str='SUPPORTED',item_id:Optional[str]=None):
        ev=evidence_ids or []; kind=item_type.upper()
        if kind in {'FACT','OBSERVED_FACT','CLASSIFICATION','INFERENCE','HYPOTHESIS','EXTERNAL_CLAIM'} and not ev: raise ValueError(f'{kind} requires evidence_ids')
        if kind in {'HYPOTHESIS'} and status=='VERIFIED': raise ValueError('Hypothesis cannot be directly VERIFIED')
        iid=item_id or f'epis_{uuid4().hex[:10]}'; now=datetime.now(timezone.utc).isoformat()
        with self.conn: self.conn.execute('INSERT INTO epistemology VALUES(?,?,?,?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET item_type=excluded.item_type,statement=excluded.statement,evidence_ids_json=excluded.evidence_ids_json,confidence=excluded.confidence,status=excluded.status',(iid,kind,statement,json.dumps(ev),confidence,status,now))
        return {'item_id':iid,'item_type':kind,'statement':statement,'evidence_ids':ev,'confidence':confidence,'status':status,'created_at':now}
    def get_epistemology_items(self,item_type:Optional[str]=None):
        rows=self.conn.execute('SELECT * FROM epistemology'+(' WHERE LOWER(item_type)=LOWER(?)' if item_type else ''),(item_type,) if item_type else ()).fetchall()
        return [{'item_id':r['item_id'],'item_type':r['item_type'],'statement':r['statement'],'evidence_ids':json.loads(r['evidence_ids_json'] or '[]'),'confidence':r['confidence'],'status':r['status'],'created_at':r['created_at']} for r in rows]
    def add_timeline_event(self,event_id:Optional[str]=None,event_date:str='',title:str='',description:str='',entity_ids:Optional[List[str]]=None,evidence_ids:Optional[List[str]]=None,confidence:float=1.0):
        ev=evidence_ids or []
        if not ev: raise ValueError('Timeline event requires evidence_ids')
        eid=event_id or f'evt_{uuid4().hex[:10]}'; ents=entity_ids or []
        with self.conn: self.conn.execute('INSERT INTO timeline_events VALUES(?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET event_date=excluded.event_date,title=excluded.title,description=excluded.description,entity_ids_json=excluded.entity_ids_json,evidence_ids_json=excluded.evidence_ids_json,confidence=excluded.confidence',(eid,event_date,title,description,json.dumps(ents),json.dumps(ev),confidence))
        return {'event_id':eid,'event_date':event_date,'title':title,'description':description,'entity_ids':ents,'evidence_ids':ev,'confidence':confidence}
    def get_timeline(self,ascending:bool=True):
        rows=self.conn.execute(f"SELECT * FROM timeline_events ORDER BY event_date {'ASC' if ascending else 'DESC'}").fetchall()
        return [{'event_id':r['event_id'],'event_date':r['event_date'],'title':r['title'],'description':r['description'],'entity_ids':json.loads(r['entity_ids_json'] or '[]'),'evidence_ids':json.loads(r['evidence_ids_json'] or '[]'),'confidence':r['confidence']} for r in rows]
    def get_entity_neighborhood(self,entity_id:str):
        ent=self.get_entity(entity_id)
        if not ent: return {'entity':None,'outgoing':[],'incoming':[],'neighbors':[]}
        outs=self.conn.execute('SELECT * FROM relationships WHERE source_id=?',(entity_id,)).fetchall(); ins=self.conn.execute('SELECT * FROM relationships WHERE target_id=?',(entity_id,)).fetchall()
        outgoing=[{'rel_id':r['rel_id'],'target_id':r['target_id'],'relation_type':r['relation_type'],'evidence_ids':json.loads(r['evidence_ids_json']),'confidence':r['confidence']} for r in outs]
        incoming=[{'rel_id':r['rel_id'],'source_id':r['source_id'],'relation_type':r['relation_type'],'evidence_ids':json.loads(r['evidence_ids_json']),'confidence':r['confidence']} for r in ins]
        ids={x['target_id'] for x in outgoing}|{x['source_id'] for x in incoming}; return {'entity':ent,'outgoing':outgoing,'incoming':incoming,'neighbors':[self.get_entity(x) for x in ids if self.get_entity(x)]}
    def query_provenance(self,evidence_id:str):
        rel=[dict(r) for r in self.conn.execute('SELECT * FROM relationships').fetchall() if evidence_id in json.loads(r['evidence_ids_json'] or '[]')]
        epi=[dict(r) for r in self.conn.execute('SELECT * FROM epistemology').fetchall() if evidence_id in json.loads(r['evidence_ids_json'] or '[]')]
        evt=[dict(r) for r in self.conn.execute('SELECT * FROM timeline_events').fetchall() if evidence_id in json.loads(r['evidence_ids_json'] or '[]')]
        return {'evidence_id':evidence_id,'total_references':len(rel)+len(epi)+len(evt),'relationships':rel,'epistemology_items':epi,'timeline_events':evt}
    def populate_foundational_records(self):
        raise RuntimeError('Hard-coded foundational business records are disabled. Use build_from_verified_evidence().')
    def build_from_verified_evidence(self,raw_dir:Union[str,Path]='D:/ABANGCOLEK/data/raw',decisions_file:Union[str,Path]='D:/ABANGCOLEK/data/jev/live_decisions.json'):
        self.clear(); raw_dir=Path(raw_dir); count=0
        if not raw_dir.exists(): return self.get_summary()
        for f in sorted(raw_dir.glob('*.json')):
            rec=json.loads(f.read_text(encoding='utf-8')); validate_raw_record(rec,require_authoritative=True); sid=rec['source_id']; platform=rec.get('source_platform','unknown'); ev_id=f'evidence:{sid}'; plat_id=f'platform:{platform}'
            self.add_entity(ev_id,'EVIDENCE',sid,metadata={'raw_hash':rec.get('raw_hash'),'source_url':rec.get('source_url'),'source_type':rec.get('source_type')})
            self.add_entity(plat_id,'PLATFORM',platform)
            self.add_relationship(ev_id,plat_id,'OBSERVED_ON',[sid],confidence=1.0,epistemology_class='OBSERVED_FACT',first_seen=rec.get('published_at') or rec.get('captured_at'))
            if rec.get('published_at'):
                self.add_timeline_event(f'evt:{sid}',str(rec['published_at']),f'Observed {rec.get("source_type","record")}',f'Verified source record {sid}',[ev_id,plat_id],[sid],1.0)
            count+=1
        dp=Path(decisions_file)
        if dp.exists():
            data=json.loads(dp.read_text(encoding='utf-8'))
            for d in data.get('decisions',[]):
                if d.get('authoritative') is not True or d.get('decision_engine')!='TYPESAFE_JEV': continue
                sid=d.get('source_evidence_id'); classified=d.get('classified',{}); self.add_epistemology_item(statement=f"JEV {d.get('evaluation_type')} classification: {json.dumps(classified,sort_keys=True)}",item_type='CLASSIFICATION',evidence_ids=[sid],confidence=1.0,status='SUPPORTED',item_id=d.get('decision_id'))
        return self.get_summary()
    def get_summary(self):
        e=self.conn.execute('SELECT COUNT(*) FROM entities').fetchone()[0]; r=self.conn.execute('SELECT COUNT(*) FROM relationships').fetchone()[0]; p=self.conn.execute('SELECT COUNT(*) FROM epistemology').fetchone()[0]; t=self.conn.execute('SELECT COUNT(*) FROM timeline_events').fetchone()[0]
        return {'db_path':str(self.db_path),'total_entities':e,'total_relationships':r,'total_epistemology_items':p,'total_timeline_events':t}

KnowledgeGraphV2=KnowledgeGraph
if __name__=='__main__':
    kg=KnowledgeGraph(); print(json.dumps(kg.build_from_verified_evidence(),indent=2)); kg.close()