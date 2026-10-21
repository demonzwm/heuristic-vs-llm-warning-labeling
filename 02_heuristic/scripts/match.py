from __future__ import annotations
import difflib, hashlib, re
from packaging.version import parse as parse_version

def normpath(value):
    parts=[]
    for part in str(value).replace('\\','/').split('/'):
        if part in ('','.'): continue
        if part=='..': raise ValueError('parent path segment')
        parts.append(part)
    return '/'.join(parts)

def eligible(a,b):
    return all(a.get(k) and b.get(k) and a[k]==b[k] for k in ('tool_name','project_name','rule_id')) and parse_version(str(b['project_version']))>parse_version(str(a['project_version']))

class Matcher:
    def __init__(self,dirs,threshold=3,context=2,similarity=.8,hash_size=30):
        self.dirs,self.threshold,self.context,self.similarity,self.hash_size=dirs,threshold,context,similarity,hash_size
        self.cache={}
    def content(self,row):
        key=(row['project_name'],row['project_version'],normpath(row['file_path']))
        if key not in self.cache:
            self.cache[key]=(self.dirs[key[:2]]/key[2]).read_text(encoding='utf-8',errors='ignore')
        return self.cache[key]
    def location(self,a,b,x,y):
        if normpath(a['file_path'])!=normpath(b['file_path']): return None
        # Restore the paper baseline's nearest-equal-line offset calculation.
        # The A-run's common tool/project/rule/version filter and full-path
        # requirement remain in match_version and above, respectively.
        matches=[]
        for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,x.split('\n'),y.split('\n')).get_opcodes():
            if tag=='equal':
                matches.extend((i1+k+1,j1+k+1) for k in range(i2-i1))
        if not matches: return None
        p,c=int(a['line_number']),int(b['line_number'])
        parent_closest=min(matches,key=lambda pair:abs(pair[0]-p))[0]
        child_closest=min(matches,key=lambda pair:abs(pair[1]-c))[1]
        po,co=p-parent_closest,c-child_closest
        if abs(po-co)>self.threshold: return None
        return dict(method='baseline_nearest_equal_offsets',coordinates='one-based lines',parent_line=p,child_line=c,parent_nearest_equal_line=parent_closest,child_nearest_equal_line=child_closest,parent_offset=po,child_offset=co,offset_difference=abs(po-co),threshold=self.threshold)
    def snippet_text(self,content,line):
        lines=content.split('\n')
        if not 1<=line<=len(lines): return None
        selected=lines[max(0,line-self.context-1):line+self.context]
        indent=min((len(z)-len(z.lstrip()) for z in selected if z.strip()),default=0)
        return '\n'.join(z[indent:] if z.strip() else z for z in selected)
    def normalize_code(self,code):
        code=re.sub(r'#.*$','',code or '',flags=re.MULTILINE)
        return '\n'.join(z.strip() for z in code.split('\n') if z.strip())
    def snippet(self,a,b,x,y):
        p=self.normalize_code(self.snippet_text(x,int(a['line_number'])))
        c=self.normalize_code(self.snippet_text(y,int(b['line_number'])))
        return difflib.SequenceMatcher(None,p,c).ratio() if p and c else 0.0
    def hash(self,a,b,x,y):
        xx,yy=x.split('\n'),y.split('\n');p,c=int(a['line_number'])-1,int(b['line_number'])-1
        if not 0<=p<len(xx) or not 0<=c<len(yy): return None
        p,c=re.findall(r'\w+',xx[p]),re.findall(r'\w+',yy[c])
        if not p or not c: return None
        for end,pp,cc in [('first',p[:self.hash_size],c[:self.hash_size]),('last',p[-self.hash_size:],c[-self.hash_size:])]:
            if hashlib.md5(' '.join(pp).encode()).digest()==hashlib.md5(' '.join(cc).encode()).digest():
                return dict(end=end,parent_tokens=len(pp),child_tokens=len(cc))
        return None
    def match_version(self,parent,candidates):
        candidates=[(i,c) for i,c in candidates if eligible(parent,c)]
        for strategy in ('Exact','Location','Snippet','Hash'):
            for idx,child in candidates:
                same=normpath(parent['file_path'])==normpath(child['file_path'])
                if strategy=='Exact': evidence={} if same and int(parent['line_number'])==int(child['line_number']) else None
                elif strategy=='Location': evidence=self.location(parent,child,self.content(parent),self.content(child)) if same else None
                elif strategy=='Snippet':
                    score=self.snippet(parent,child,self.content(parent),self.content(child))
                    evidence=dict(similarity=score,threshold=self.similarity) if score>=self.similarity else None
                else: evidence=self.hash(parent,child,self.content(parent),self.content(child))
                if evidence is not None: return strategy,idx,child,evidence
        return None
