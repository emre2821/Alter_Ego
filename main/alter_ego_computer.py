#!/usr/bin/env python3
# alter_ego_computer.py
# Local RAG assistant with MemoryDB, dupes scanner, and upgrade suggestions.
# 100% local; backends: transformers (CPU), gpt4all, or ollama (HTTP).
# License: MIT

from __future__ import annotations
import os, sys, time, json, hashlib, threading, queue, re, textwrap, shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box

from pydantic import BaseModel
import yaml

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Optional imports guarded:
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_OK = True
except Exception:
    WATCHDOG_OK = False

# Optional LLM backends
BACKENDS = {"transformers", "gpt4all", "ollama"}

console = Console()

# --------- Custom Palettes (CLI + future GUI theming) ----------
PALETTES = {
    "eden_moonlit": {
        "accent": "violet",
        "ok": "green",
        "warn": "yellow",
        "err": "red",
        "muted": "grey50",
        "info": "cyan",
        "title": "bright_white",
        "dim": "grey58",
    },
    "eden_sunrise": {
        "accent": "magenta",
        "ok": "bright_green",
        "warn": "gold1",
        "err": "bright_red",
        "muted": "grey54",
        "info": "bright_cyan",
        "title": "white",
        "dim": "grey62",
    },
    "eden_void": {
        "accent": "deep_sky_blue1",
        "ok": "spring_green2",
        "warn": "khaki1",
        "err": "red3",
        "muted": "grey39",
        "info": "turquoise2",
        "title": "white",
        "dim": "grey54",
    },
}
DEFAULT_PALETTE = "eden_moonlit"

# --------- Config schema ----------
class Config(BaseModel):
    data_dir: str = "./data"
    db_dir: str = "./emma_db"
    palette: str = DEFAULT_PALETTE
    embed_model_name: str = "all-MiniLM-L6-v2"
    llm_backend: str = "transformers"  # transformers | gpt4all | ollama
    llm_model_name: str = "microsoft/phi-3-mini-4k-instruct"  # or GPT4All .bin name, or Ollama tag
    top_k: int = 5
    chunk_chars: int = 1200
    chunk_overlap: int = 200
    collections: Dict[str, str] = {
        "docs": "emma_docs",
        "mem": "emma_memories",
        "states": "emma_state_notes",
    }
    allowed_exts: List[str] = [
        ".txt", ".md", ".rst", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".css", ".html", ".sql", ".env",
        ".chaos", ".vas",
    ]
    ignore_globs: List[str] = [
        "**/.git/**", "**/__pycache__/**", "**/.venv/**", "**/node_modules/**",
        "**/*.lock", "**/*.log"
    ]
    max_ctx_chars: int = 8000
    suggest_threshold_dupes: int = 3  # if ≥N dupes with same name -> suggest action
    min_near_dup_sim: float = 0.985   # cosine sim threshold for near-duplicate chunks

# --------- Utility ----------
def load_config(cfg_path: Path) -> Config:
    if cfg_path.exists():
        data = yaml.safe_load(cfg_path.read_text())
        return Config(**data)
    cfg = Config()
    cfg_path.write_text(yaml.safe_dump(cfg.dict(), sort_keys=False))
    return cfg

def save_config(cfg_path: Path, cfg: Config):
    cfg_path.write_text(yaml.safe_dump(cfg.dict(), sort_keys=False))

def sha1_bytes(b: bytes) -> str:
    h = hashlib.sha1()
    h.update(b)
    return h.hexdigest()

def sha1_file(p: Path) -> str:
    with p.open("rb") as f:
        return sha1_bytes(f.read())

def read_text_file(p: Path) -> str:
    # lenient reader that treats JSON/YAML as text
    try:
        raw = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = p.read_text(encoding="latin-1", errors="ignore")
    return raw

def clean_text(s: str) -> str:
    s = s.replace("\r\n", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def chunk_text(txt: str, size: int, overlap: int) -> List[str]:
    txt = clean_text(txt)
    if len(txt) <= size:
        return [txt]
    chunks = []
    i = 0
    while i < len(txt):
        chunk = txt[i:i+size]
        chunks.append(chunk)
        i += (size - overlap)
    return chunks

def within_any_glob(path: Path, patterns: List[str]) -> bool:
    from fnmatch import fnmatch
    s = str(path.as_posix())
    return any(fnmatch(s, pat) for pat in patterns)

def now_iso() -> str:
    import datetime as dt
    return dt.datetime.now().isoformat(timespec="seconds")

# --------- Embeddings ----------
class Embedder:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=False).tolist()

# --------- Vector DB ----------
class MemoryBank:
    def __init__(self, cfg: Config):
        self.client = chromadb.PersistentClient(
            path=cfg.db_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.cfg = cfg
        self.docs = self._get_collection(cfg.collections["docs"])
        self.mem = self._get_collection(cfg.collections["mem"])
        self.state = self._get_collection(cfg.collections["states"])

    def _get_collection(self, name: str):
        try:
            return self.client.get_collection(name=name, metadata={"hnsw:space":"cosine"})
        except chromadb.errors.InvalidCollectionException:
            return self.client.create_collection(name=name, metadata={"hnsw:space":"cosine"})

# --------- LLM Backends ----------
class LLM:
    def __init__(self, backend: str, model_name: str):
        self.backend = backend
        self.model_name = model_name
        self._init_backend()

    def _init_backend(self):
        if self.backend == "gpt4all":
            try:
                from gpt4all import GPT4All
                self.engine = GPT4All(self.model_name)
                return
            except Exception as e:
                raise RuntimeError(f"GPT4All not available: {e}")
        elif self.backend == "transformers":
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                tok = AutoTokenizer.from_pretrained(self.model_name)
                mdl = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype="auto", device_map="auto")
                self.pipe = pipeline("text-generation", model=mdl, tokenizer=tok)
                return
            except Exception as e:
                raise RuntimeError(f"Transformers backend failed: {e}")
        elif self.backend == "ollama":
            # Lazy: no init, we’ll hit HTTP endpoint on call
            return
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        if self.backend == "gpt4all":
            return self.engine.generate(prompt, max_tokens=max_tokens, temp=temperature)
        elif self.backend == "transformers":
            out = self.pipe(
                prompt,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=self.pipe.tokenizer.eos_token_id,
            )
            # pipeline returns list of dicts
            text = out[0]["generated_text"]
            # Return the tail after the prompt if present
            return text[len(prompt):].strip() if text.startswith(prompt) else text
        elif self.backend == "ollama":
            import json as _json, urllib.request as _url, urllib.error as _err
            url = "http://localhost:11434/api/generate"
            payload = _json.dumps({"model": self.model_name, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}).encode("utf-8")
            req = _url.Request(url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with _url.urlopen(req, timeout=600) as resp:
                    data = _json.loads(resp.read().decode("utf-8"))
                    return data.get("response", "").strip()
            except _err.URLError as e:
                raise RuntimeError(f"Ollama HTTP error: {e}")
        else:
            raise ValueError("Invalid backend")

# --------- Core RAG flow ----------
SYSTEM_VIBE = (
    "You are Emma’s Computer. Supportive, precise, and emotionally aware. "
    "You use the memorybank to recall facts. If the user seems overwhelmed, you slow down, "
    "offer micro-steps, and ask gentle consent questions. Be concise. No hallucinations."
)

def make_prompt(context_chunks: List[str], question: str) -> str:
    ctx = "\n".join(f"- {c}" for c in context_chunks)
    return f"""[system]
{SYSTEM_VIBE}

[context from Emma’s files and memories]
{ctx}

[instruction]
Answer the question using the context when relevant. If unsure, say so briefly.
End with a one-line check-in if emotional load seems high.

[question]
{question}

[answer as Emma’s Computer]
"""

def retrieve_context(bank: MemoryBank, embedder: Embedder, query: str, top_k: int) -> List[str]:
    qvec = embedder.embed_texts([query])[0]
    contexts = []
    for coll in (bank.docs, bank.mem):
        res = coll.query(query_embeddings=[qvec], n_results=top_k)
        for doc, md in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]):
            snippet = doc[:800]
            tag = md.get("tag", "doc")
            src = md.get("path") or md.get("source") or md.get("id","")
            contexts.append(f"[{tag}] {snippet}\n(src: {src})")
    # keep max by length budget
    joined = []
    budget = 6000
    used = 0
    for c in contexts:
        if used + len(c) <= budget:
            joined.append(c)
            used += len(c)
    return joined[:max(3, top_k)]

# --------- Ingestion ----------
def ingest_path(cfg: Config, bank: MemoryBank, embedder: Embedder, path: Path):
    files = []
    if path.is_file():
        files = [path]
    else:
        for p in path.rglob("*"):
            if p.is_file():
                if within_any_glob(p, cfg.ignore_globs): 
                    continue
                if p.suffix.lower() in cfg.allowed_exts:
                    files.append(p)
    if not files:
        console.print("[yellow]No files matched for ingestion.[/yellow]")
        return

    docs_ids, docs, metas = [], [], []
    for p in files:
        try:
            txt = read_text_file(p)
        except Exception as e:
            console.print(f"[red]Failed to read {p}: {e}[/red]")
            continue
        if not txt.strip():
            continue
        chunks = chunk_text(txt, cfg.chunk_chars, cfg.chunk_overlap)
        file_hash = sha1_file(p)
        for i, ch in enumerate(chunks):
            cid = f"{file_hash}:{i}"
            docs_ids.append(cid)
            docs.append(ch)
            metas.append({
                "path": str(p),
                "file_sha1": file_hash,
                "chunk_index": i,
                "tag": "doc",
                "mtime": os.path.getmtime(p),
            })

    if not docs:
        console.print("[yellow]Nothing to add.[/yellow]")
        return

    console.print(f"[cyan]Embedding {len(docs)} chunks...[/cyan]")
    vecs = embedder.embed_texts(docs)
    bank.docs.upsert(ids=docs_ids, embeddings=vecs, metadatas=metas, documents=docs)
    console.print(f"[green]Ingested {len(docs)} chunks from {len(files)} files.[/green]")

# --------- Watcher ----------
class _Handler(FileSystemEventHandler):
    def __init__(self, cfg: Config, bank: MemoryBank, embedder: Embedder):
        self.cfg = cfg
        self.bank = bank
        self.embedder = embedder

    def on_modified(self, event):
        self._maybe_ingest(event)

    def on_created(self, event):
        self._maybe_ingest(event)

    def _maybe_ingest(self, event):
        if event.is_directory: 
            return
        p = Path(event.src_path)
        if within_any_glob(p, self.cfg.ignore_globs): 
            return
        if p.suffix.lower() not in self.cfg.allowed_exts:
            return
        console.print(f"[magenta]Detected change: {p}[/magenta]")
        ingest_path(self.cfg, self.bank, self.embedder, p)

def watch_path(cfg: Config, bank: MemoryBank, embedder: Embedder, path: Path):
    if not WATCHDOG_OK:
        console.print("[red]watchdog is not installed; cannot watch.[/red]")
        return
    event_handler = _Handler(cfg, bank, embedder)
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()
    console.print(f"[cyan]Watching {path}... Press Ctrl+C to stop.[/cyan]")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --------- Memory auto-save ----------
def save_memory(bank: MemoryBank, embedder: Embedder, text: str, tag: str = "memory", source: str = "auto"):
    vec = embedder.embed_texts([text])[0]
    mid = sha1_bytes(text.encode("utf-8")) + ":" + now_iso()
    bank.mem.upsert(ids=[mid], embeddings=[vec], metadatas=[{"tag": tag, "source": source}], documents=[text])

def save_state_note(bank: MemoryBank, embedder: Embedder, text: str, subtype: str):
    vec = embedder.embed_texts([text])[0]
    sid = sha1_bytes((text+subtype).encode("utf-8")) + ":" + now_iso()
    bank.state.upsert(ids=[sid], embeddings=[vec], metadatas=[{"tag": "state", "subtype": subtype}], documents=[text])

# --------- Dupe & drift tools ----------
def scan_dupes(cfg: Config, bank: MemoryBank) -> Dict[str, Any]:
    # 1) filename dupes
    name_to_paths: Dict[str, List[str]] = {}
    for p in Path(cfg.data_dir).rglob("*"):
        if p.is_file() and p.suffix.lower() in cfg.allowed_exts and not within_any_glob(p, cfg.ignore_globs):
            name_to_paths.setdefault(p.name, []).append(str(p))

    filename_dupes = {k:v for k,v in name_to_paths.items() if len(v) >= 2}

    # 2) content dupes via file hash
    hash_to_paths: Dict[str, List[str]] = {}
    for p in Path(cfg.data_dir).rglob("*"):
        if p.is_file() and p.suffix.lower() in cfg.allowed_exts and not within_any_glob(p, cfg.ignore_globs):
            try:
                h = sha1_file(p)
                hash_to_paths.setdefault(h, []).append(str(p))
            except Exception:
                pass
    exact_dupes = {k:v for k,v in hash_to_paths.items() if len(v) >= 2}

    # 3) vector near-duplicates (within docs collection)
    # Chroma doesn’t expose direct “near-dup all-pairs” easily; we’ll approximate by sampling ids by file hash prefix
    # Practical: we warn and let user run a targeted consolidation later.
    # We still report the threshold being used.
    near_dup_threshold = cfg.min_near_dup_sim

    return {
        "filename_dupes": filename_dupes,
        "exact_dupes": exact_dupes,
        "near_dup_info": {
            "threshold": near_dup_threshold,
            "note": "Near-duplicate chunk scan is interactive; use `consolidate` with --by-sim to process by similarity."
        }
    }

def consolidate_files(strategy: str, only_list: bool, filename_dupes: Dict[str, List[str]]):
    # strategy: newest | oldest | keep_first
    actions = []
    for name, paths in filename_dupes.items():
        # sort by mtime
        times = [(p, os.path.getmtime(p)) for p in paths]
        times.sort(key=lambda x: x[1])
        if strategy == "newest":
            keep = times[-1][0]
        elif strategy == "oldest":
            keep = times[0][0]
        else:
            keep = paths[0]
        to_remove = [p for p in paths if p != keep]
        actions.append((name, keep, to_remove))

    if only_list:
        for (name, keep, to_remove) in actions:
            console.print(Panel.fit(
                f"[bold]{name}[/bold]\nKeep: {keep}\nDelete: {len(to_remove)} file(s):\n" + "\n".join(to_remove),
                title="Plan", border_style="yellow", box=box.SQUARE))
        return

    for (name, keep, to_remove) in actions:
        console.print(Panel.fit(f"[bold]{name}[/bold]\nKeeping: {keep}", title="Consolidating", border_style="cyan"))
        for p in to_remove:
            if Confirm.ask(f"Delete duplicate: {p} ?", default=False):
                try:
                    os.remove(p)
                    console.print(f"[green]Deleted {p}[/green]")
                except Exception as e:
                    console.print(f"[red]Failed to delete {p}: {e}[/red]")

# --------- Upgrade suggestions ----------
def suggest_upgrades(cfg: Config, bank: MemoryBank) -> List[str]:
    suggestions = []
    # Heuristics
    # 1) too many chunks, consider larger embed model or tighter chunk size
    # 2) DB not persisted? (we persist)
    # 3) embedding model modernity
    # 4) duplicates threshold
    # 5) backups
    # 6) watcher not running long enough
    # 7) missing memories

    # count docs
    try:
        count_docs = bank.docs.count()
    except Exception:
        count_docs = None

    if count_docs and count_docs > 20000:
        suggestions.append(f"Docs are {count_docs} chunks. Consider increasing chunk size from {cfg.chunk_chars} to ~1600 or enabling selective folders.")

    if cfg.embed_model_name.lower() in {"all-minilm-l6-v2"}:
        suggestions.append("Embedding model is all-MiniLM-L6-v2. It’s fast, but you may get better retrieval with bge-small-en or e5-small (still free).")

    # duplicates quick-check
    dupes = scan_dupes(cfg, bank)
    if dupes["filename_dupes"]:
        worst = max(len(v) for v in dupes["filename_dupes"].values())
        if worst >= cfg.suggest_threshold_dupes:
            suggestions.append(f"You have ≥{cfg.suggest_threshold_dupes} duplicates for some filenames (max seen: {worst}). Consider running `scan-dupes` then `consolidate --strategy newest`.")

    # backups
    if not Path(cfg.db_dir, "BACKUP").exists():
        suggestions.append("No DB backup detected. Consider `rsync -a emma_db/ emma_db/BACKUP/` weekly.")

    # memories presence
    try:
        mem_count = bank.mem.count()
        if mem_count < 10:
            suggestions.append("MemoryDB is light. Enable auto-save (default) by using the `ask` command regularly; it will store brief summaries.")
    except Exception:
        pass

    return suggestions

# --------- CLI ----------
app = typer.Typer(add_completion=False, no_args_is_help=True)

def palette(cfg: Config):
    return PALETTES.get(cfg.palette, PALETTES[DEFAULT_PALETTE])

def banner(cfg: Config):
    pal = palette(cfg)
    console.print(Panel.fit(
        "[b]Emma’s Computer[/b]\nLocal RAG • MemoryDB • Dupe Scanner • Upgrades",
        title="[b]Paradigm Eden[/b]", border_style=pal["accent"])
    )

@app.command()
def init(
    data: str = typer.Option("./data", help="Folder to ingest/watch"),
    db: str = typer.Option("./emma_db", help="ChromaDB persistence dir"),
    palette_name: str = typer.Option(DEFAULT_PALETTE, help=f"One of: {', '.join(PALETTES.keys())}")
):
    cfg_path = Path("emma_config.yaml")
    cfg = load_config(cfg_path)
    cfg.data_dir = data
    cfg.db_dir = db
    if palette_name in PALETTES:
        cfg.palette = palette_name
    Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.db_dir).mkdir(parents=True, exist_ok=True)
    save_config(cfg_path, cfg)
    banner(cfg)
    console.print(f"Config saved -> [cyan]{cfg_path}[/cyan]")
    console.print(f"Data dir      -> [cyan]{cfg.data_dir}[/cyan]")
    console.print(f"DB dir        -> [cyan]{cfg.db_dir}[/cyan]")

@app.command()
def ingest(path: str = typer.Argument(..., help="File or folder to ingest")):
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)
    ingest_path(cfg, bank, embedder, Path(path))
    # record a state note
    save_state_note(bank, embedder, f"Ingested path {path} at {now_iso()}", "ingest")

@app.command("watch")
def watch_cmd(path: str = typer.Argument(None, help="Folder to watch (defaults to config data_dir)")):
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)
    root = Path(path) if path else Path(cfg.data_dir)
    watch_path(cfg, bank, embedder, root)

@app.command()
def ask(
    question: str = typer.Argument(...),
    backend: str = typer.Option(None, help="transformers | gpt4all | ollama"),
    model_name: str = typer.Option(None, help="Model id or file (backend-specific)"),
    max_tokens: int = typer.Option(512),
    temperature: float = typer.Option(0.7),
):
    cfg = load_config(Path("emma_config.yaml"))
    if backend: cfg.llm_backend = backend
    if model_name: cfg.llm_model_name = model_name
    banner(cfg)
    pal = palette(cfg)

    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)
    ctx = retrieve_context(bank, embedder, question, cfg.top_k)
    prompt = make_prompt(ctx, question)

    console.print(Panel.fit("Retrieving + thinking...", border_style=pal["muted"]))
    try:
        llm = LLM(cfg.llm_backend, cfg.llm_model_name)
        answer = llm.generate(prompt, max_tokens=max_tokens, temperature=temperature)
    except Exception as e:
        console.print(f"[red]LLM error:[/red] {e}")
        return

    console.print(Panel.fit(answer.strip(), title="Answer", border_style=pal["ok"], box=box.SQUARE))

    # auto-save memory: brief note
    memory_note = f"Q: {question}\nA: {answer[:600]}"
    save_memory(bank, embedder, memory_note, tag="chat", source="ask")

    # gentle check-in hook (very small heuristic)
    if any(w in question.lower() for w in ["overwhelmed","stuck","tired","spiral","anxious","panic","can't","cannot"]):
        console.print(f"[{pal['warn']}]um… hey. can we slow it down? want micro-steps or for me to carry the next step?[/]")

@app.command("scan-dupes")
def scan_dupes_cmd():
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    report = scan_dupes(cfg, bank)
    pal = palette(cfg)

    # filename dupes
    t = Table(title="Filename Duplicates", box=box.SIMPLE_HEAVY)
    t.add_column("Name", style=pal["title"])
    t.add_column("#", style=pal["info"], justify="right")
    t.add_column("Paths", style=pal["dim"])
    if report["filename_dupes"]:
        for name, paths in sorted(report["filename_dupes"].items(), key=lambda kv: -len(kv[1])):
            t.add_row(name, str(len(paths)), "\n".join(paths[:5]) + ("..." if len(paths) > 5 else ""))
    else:
        t.add_row("—", "0", "No filename dupes found.")
    console.print(t)

    # exact dupes
    t2 = Table(title="Exact Content Duplicates (SHA1)", box=box.SIMPLE_HEAVY)
    t2.add_column("SHA1", style=pal["title"])
    t2.add_column("#", style=pal["info"], justify="right")
    t2.add_column("Paths", style=pal["dim"])
    if report["exact_dupes"]:
        for h, paths in sorted(report["exact_dupes"].items(), key=lambda kv: -len(kv[1])):
            t2.add_row(h[:12]+"…", str(len(paths)), "\n".join(paths[:5]) + ("..." if len(paths) > 5 else ""))
    else:
        t2.add_row("—", "0", "No exact dupes found.")
    console.print(t2)

    console.print(Panel.fit(
        f"Near-duplicates: cosine ≥ {report['near_dup_info']['threshold']}\n"
        f"{report['near_dup_info']['note']}",
        border_style=pal["muted"]))

    # Save a state note and a friendly nudge
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)
    save_state_note(bank, embedder, f"Dupe scan at {now_iso()}", "dupe-scan")

    if report["filename_dupes"]:
        console.print(f"[{pal['warn']}]um… girl… you have {len(report['filename_dupes'])} filename groups with duplicates. consolidate? delete? or just list paths? and… you ok?[/]")

@app.command()
def consolidate(
    strategy: str = typer.Option("newest", help="newest | oldest | keep_first"),
    only_paths: bool = typer.Option(False, help="Just print plan; don’t delete")
):
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    report = scan_dupes(cfg, bank)
    consolidate_files(strategy=strategy, only_list=only_paths, filename_dupes=report["filename_dupes"])

@app.command("list-dupes")
def list_dupes(only_paths: bool = typer.Option(True, help="Only print paths")):
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    report = scan_dupes(cfg, bank)
    pal = palette(cfg)
    for name, paths in report["filename_dupes"].items():
        console.print(Panel("\n".join(paths), title=f"{name} ({len(paths)})", border_style=pal["warn"]))
    for h, paths in report["exact_dupes"].items():
        console.print(Panel("\n".join(paths), title=f"SHA1:{h[:12]}… ({len(paths)})", border_style=pal["muted"]))

@app.command("suggest")
def suggest():
    cfg = load_config(Path("emma_config.yaml"))
    banner(cfg)
    bank = MemoryBank(cfg)
    sugg = suggest_upgrades(cfg, bank)
    if not sugg:
        console.print("[green]No upgrade suggestions right now.[/green]")
        return
    for s in sugg:
        console.print(f"• {s}")
    # Auto-save
    embedder = Embedder(cfg.embed_model_name)
    save_memory(bank, embedder, "Upgrade suggestions:\n" + "\n".join(f"- {x}" for x in sugg), tag="upgrade", source="auto")

@app.command("config")
def config_cmd(show: bool = typer.Option(True), set_backend: Optional[str] = None, set_model: Optional[str] = None, set_palette: Optional[str] = None):
    cfg_path = Path("emma_config.yaml")
    cfg = load_config(cfg_path)
    changed = False
    if set_backend:
        if set_backend not in BACKENDS:
            console.print(f"[red]Invalid backend. Choose from: {', '.join(BACKENDS)}[/red]")
            raise typer.Exit(code=1)
        cfg.llm_backend = set_backend; changed = True
    if set_model:
        cfg.llm_model_name = set_model; changed = True
    if set_palette:
        if set_palette not in PALETTES:
            console.print(f"[red]Invalid palette. Choose from: {', '.join(PALETTES.keys())}[/red]")
            raise typer.Exit(code=1)
        cfg.palette = set_palette; changed = True
    if changed:
        save_config(cfg_path, cfg)
        console.print("[green]Config updated.[/green]")
    if show:
        banner(cfg)
        console.print(yaml.safe_dump(cfg.dict(), sort_keys=False))

if __name__ == "__main__":
    app()
