See Compare data types for advice on which of the general-purpose data types is best for common tasks.
### Strings https://redis.io/docs/latest/develop/data-types/#strings "Copy link to clipboard"
Redis strings are the most basic Redis data type, representing a sequence of bytes. For more information, see:
* Overview of Redis strings
* Redis string command reference

### Bitfields https://redis.io/docs/latest/develop/data-types/#bitfields "Copy link to clipboard"
Redis bitfields efficiently encode multiple counters in a string value. Bitfields provide atomic get, set, and increment operations and support different overflow policies. For more information, see:
* Overview of Redis bitfields
* The `BITFIELD` command.

### Bitmaps https://redis.io/docs/latest/develop/data-types/#bitmaps "Copy link to clipboard"
Redis bitmaps let you perform bitwise operations on strings. For more information, see:
* Overview of Redis bitmaps
* Redis bitmap command reference

### Arrays https://redis.io/docs/latest/develop/data-types/#arrays "Copy link to clipboard"
Redis arrays are sparse, index-addressable sequences of strings. For more information, see:
* Overview of Redis arrays
* Redis array command reference

### Geospatial indexes https://redis.io/docs/latest/develop/data-types/#geospatial-indexes "Copy link to clipboard"
Redis geospatial indexes are useful for finding locations within a given geographic radius or bounding box. For more information, see:
* Overview of Redis geospatial indexes
* Redis geospatial indexes command reference

### Hashes https://redis.io/docs/latest/develop/data-types/#hashes "Copy link to clipboard"
Redis hashes are record types modeled as collections of field-value pairs. As such, Redis hashes resemble Python dictionaries, Java HashMaps, and Ruby hashes. For more information, see:
* Overview of Redis hashes
* Redis hashes command reference

### JSON https://redis.io/docs/latest/develop/data-types/#json "Copy link to clipboard"
Redis JSON provides structured, hierarchical arrays and key-value objects that match the popular JSON text file format. You can import JSON text into Redis objects and access, modify, and query individual data elements. For more information, see:
* Overview of Redis JSON
* JSON command reference

### Lists https://redis.io/docs/latest/develop/data-types/#lists "Copy link to clipboard"
Redis lists are lists of strings sorted by insertion order. For more information, see:
* Overview of Redis lists
* Redis list command reference

### Bloom filter https://redis.io/docs/latest/develop/data-types/#bloom-filter "Copy link to clipboard"
Redis Bloom filters let you check for the presence or absence of an element in a set. For more information, see:
* Overview of Redis Bloom filters
* Bloom filter command reference

### Count-min sketch https://redis.io/docs/latest/develop/data-types/#count-min-sketch "Copy link to clipboard"
Redis Count-min sketch estimate the frequency of a data point within a stream of values. For more information, see:
* Redis Count-min sketch overview
* Count-min sketch command reference

### Cuckoo filter https://redis.io/docs/latest/develop/data-types/#cuckoo-filter "Copy link to clipboard"
Redis Cuckoo filters let you check for the presence or absence of an element in a set. They are similar to Bloom filters but with slightly different trade-offs between features and performance. For more information, see:
* Overview of Redis Cuckoo filters
* Cuckoo filter command reference

### HyperLogLog https://redis.io/docs/latest/develop/data-types/#hyperloglog "Copy link to clipboard"
The Redis HyperLogLog data structures provide probabilistic estimates of the cardinality (i.e., number of elements) of large sets. For more information, see:
* Overview of Redis HyperLogLog
* Redis HyperLogLog command reference

### t-digest https://redis.io/docs/latest/develop/data-types/#t-digest "Copy link to clipboard"
Redis t-digest structures estimate percentiles from a stream of data values. For more information, see:
* Redis t-digest overview
* t-digest command reference

### Top-K https://redis.io/docs/latest/develop/data-types/#top-k "Copy link to clipboard"
Redis Top-K structures estimate the ranking of a data point within a stream of values. For more information, see:
* Redis Top-K overview
* Top-K command reference

### Sets https://redis.io/docs/latest/develop/data-types/#sets "Copy link to clipboard"
Redis sets are unordered collections of unique strings that act like the sets from your favorite programming language (for example, Java HashSets, Python sets, and so on). With a Redis set, you can add, remove, and test for existence in O(1) time (in other words, regardless of the number of set elements). For more information, see:
* Overview of Redis sets
* Redis set command reference

### Sorted sets https://redis.io/docs/latest/develop/data-types/#sorted-sets "Copy link to clipboard"
Redis sorted sets are collections of unique strings that maintain order by each string's associated score. For more information, see:
* Overview of Redis sorted sets
* Redis sorted set command reference

### Streams https://redis.io/docs/latest/develop/data-types/#streams "Copy link to clipboard"
A Redis stream is a data structure that acts like an append-only log. Streams help record events in the order they occur and then syndicate them for processing. For more information, see:
* Overview of Redis Streams
* Redis Streams command reference

### Time series https://redis.io/docs/latest/develop/data-types/#time-series "Copy link to clipboard"
Redis time series structures let you store and query timestamped data points. For more information, see:
* Redis time series overview
* Time series command reference

### Vector sets https://redis.io/docs/latest/develop/data-types/#vector-sets "Copy link to clipboard"
Redis vector sets are a specialized data type designed for managing high-dimensional vector data, enabling fast and efficient vector similarity search within Redis. Vector sets are optimized for use cases involving machine learning, recommendation systems, and semantic search, where each vector represents a data point in multi-dimensional space. Vector sets supports the HNSW (hierarchical navigable small world) algorithm, allowing you to store, index, and query vectors based on the cosine similarity metric. With vector sets, Redis provides native support for hybrid search, combining vector similarity with structured filters. For more information, see:
* Overview of Redis vector sets
* Redis vector set command reference

## Adding extensions https://redis.io/docs/latest/develop/data-types/#adding-extensions "Copy link to clipboard"
To extend the features provided by the included data types, use one of these options:
1. Write your own custom server-side functions in Lua.
2. Write your own Redis module using the modules API or check out the community-supported modules.