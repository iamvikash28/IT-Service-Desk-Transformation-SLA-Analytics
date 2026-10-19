import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.db import query_all
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report,accuracy_score
import joblib
rows=query_all("SELECT description,category FROM support_tickets WHERE description IS NOT NULL AND category IS NOT NULL")
if len(rows)<30 or len({r["category"] for r in rows})<2:raise SystemExit("Seed 30+ tickets across 2+ categories first.")
X=[r["description"] for r in rows];y=[r["category"] for r in rows]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
model=Pipeline([("tfidf",TfidfVectorizer(ngram_range=(1,2),lowercase=True,strip_accents="unicode")),("classifier",LogisticRegression(max_iter=1000,class_weight="balanced"))])
model.fit(Xtr,ytr);pred=model.predict(Xte)
report=f"Rows: {len(rows)}\nTrain: {len(Xtr)}\nTest: {len(Xte)}\nAccuracy: {accuracy_score(yte,pred):.4f}\n\n{classification_report(yte,pred,zero_division=0)}\nSynthetic-data limitation: results do not establish real-world performance.\n"
out=ROOT/"reports";out.mkdir(exist_ok=True);(out/"classifier_evaluation.txt").write_text(report,encoding="utf-8")
mdir=ROOT/"app"/"models";mdir.mkdir(exist_ok=True);joblib.dump(model,mdir/"ticket_classifier.joblib")
print(report);print(f"Saved model: {mdir/'ticket_classifier.joblib'}")
