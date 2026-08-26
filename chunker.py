def tok_len(s: str) -> int:
    return max(1, len(s) // 4)          # good-enough estimate
 
def chunk(text: str, max_tokens: int = 350,
          overlap: int = 50) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if buf and tok_len(buf) + tok_len(p) > max_tokens:
            chunks.append(buf.strip())
            buf = buf[-overlap * 4:]     # tail as overlap
        buf += "\n\n" + p
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


if __name__ == "__main__":                                                                                                                                                                                              
       import sys                                                                                                                                                                                                          
       from pathlib import Path                                                                                                                                                                                            
       for path in sys.argv[1:]:                                                                                                                                                                                           
           text = Path(path).read_text(errors="ignore")                                                                                                                                                                    
           for i, c in enumerate(chunk(text)):                                                                                                                                                                             
               print(f"=== {path} chunk {i} ({tok_len(c)} tok) ===\n{c}\n") 