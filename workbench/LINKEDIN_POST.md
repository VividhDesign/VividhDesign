# LinkedIn / X post drafts (post after pushing Strata 0.2.0)

## LinkedIn (about 180 words)

Strata 0.2.0 is out. It's the vector database I've been building from scratch in C++17.

Three things I'd been apologising for in the README are fixed:

🔹 **8-bit quantization with exact re-ranking.** The graph stores one byte per dimension. On 400k GloVe vectors
(300-d) it keeps float recall with 43–56% more queries per second. With the re-rank vectors memory-mapped, private
RAM drops from 537 MB to 197 MB.

🔹 **Writes no longer block reads.** During an 18-second bulk insert, a query thread used to get 2 answers. Now it gets
81,561, with p99 latency of 0.46 ms. Verified with ThreadSanitizer.

🔹 **Smarter filtered search.** A cost model decides between graph walk and brute force. Filtered queries at 2%
selectivity got 7–25× faster with exact results.

Compared with FAISS's 8-bit HNSW at the same size, Strata answers ~4× more queries per second. FAISS's float index
still beats mine at high recall on 300-d data, and the README says so.

Code, benchmarks and design notes: github.com/VividhDesign/strata

#VectorSearch #Databases #CPlusPlus #RAG #OpenSource

## X / Twitter (one post)

Strata 0.2.0: my from-scratch C++ vector DB now does 8-bit quantization with exact rerank (2.7× less RAM, same
recall), lets queries keep running during bulk inserts (p99 0.46 ms vs blocked), and picks brute force vs graph walk
by cost for filters (7–25× faster at 2%). github.com/VividhDesign/strata

## Optional disclosure line

> Built with AI pair-programming (Claude Code). Every number is reproducible from `bench/` in the repo.

Adding it costs nothing and protects your credibility if anyone asks.
