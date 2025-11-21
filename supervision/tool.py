import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from supervision.card.Setting import cfg

_PROCESSED_INDICES = set()


def _ensure_dir(p):
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def is_processed(index):
    return index in _PROCESSED_INDICES


def clear_processed_cache():
    _PROCESSED_INDICES.clear()


def _build_output_path(input_path):
    inp = Path(input_path)
    out_dir = Path(cfg.get(cfg.saveFolder))
    _ensure_dir(out_dir)
    return out_dir / inp.name


def _run_sv(input_path, model, output_path, extra_args):
    cmd = [r"./bin/YoloByETO.exe", "-i", str(input_path)]
    if model:
        cmd += ["-m", Path(cfg.get(cfg.modelFolder)) / str(model)]

    cmd += ["-o", str(output_path)]
    if extra_args:
        cmd += ["-j", str(extra_args)]

    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"YoloByETO.exe failed for {input_path}: {e}")
        return False


def process_file_once(index, input_path, model=None, extra_args=None):
    if not input_path:
        return None
    if is_processed(index):
        return None
    if model is None:
        model = cfg.get(cfg.modelChoice)

    out_path = _build_output_path(input_path)
    success = _run_sv(input_path, model, str(out_path), extra_args)
    if success:
        _PROCESSED_INDICES.add(index)
        return index, str(out_path)
    return None


def process_files_threaded(indices, files, max_workers=4, model=None, extra_args=None):
    if model is None:
        model = cfg.get(cfg.modelChoice)

    futures = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for idx, i in enumerate(indices):
            key = i
            try:
                input_path = files[idx]
            except Exception:
                input_path = ''
            if not input_path or is_processed(key):
                continue
            futures[ex.submit(process_file_once, key, input_path, model, extra_args)] = key

    results_map = {}
    for fut in as_completed(futures):
        res = fut.result()
        if res:
            k, outp = res
            results_map[k] = outp

    out_list = []
    for idx, key in enumerate(indices):
        if key in results_map:
            out_list.append((key, results_map[key]))

    return out_list
