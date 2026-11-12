import sys


def peak_memory_mb():
    """Highest memory this program has used, in MiB (None if the system cannot tell)."""
    try:
        import resource
    except ImportError:                       # Windows has no `resource` module
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024   # macOS: bytes, Linux: KB


def format_summary(name, seconds, paragraphs, errors, usage):
    memory = peak_memory_mb()
    memory_text = f"{memory:.1f} MiB" if memory is not None else "n/a"
    return (
        f"--- Performance summary for {name} ---\n"
        f"  time         : {seconds:.2f}s\n"
        f"  peak memory  : {memory_text}\n"
        f"  paragraphs   : {paragraphs}\n"
        f"  errors tagged: {errors}\n"
        f"  model calls  : {usage['calls']} "
        f"({usage['input_tokens']} tokens in, {usage['output_tokens']} out, "
        f"{usage['cache_read_tokens']} read from prompt cache)"
    )