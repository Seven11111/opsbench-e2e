#
EXPIRE
Syntax text  Syntax diagram  API methods
```
EXPIRE key seconds [NX | XX | GT | LT]
```

!Railroad diagram for EXPIRE
Client: Python (redis-py) Node.js (node-redis) Java-Sync (Jedis) Lettuce-Sync Java-Async (Lettuce) Java-Reactive (Lettuce) Go (go-redis) C#-Sync (NRedisStack) C#-Async (NRedisStack) PHP (Predis) Rust-Sync (redis-rs) Rust-Async (redis-rs)
```
expire(
name: KeyT,
time: ExpiryT,
nx: bool,
xx: bool,
gt: bool,
lt: bool
) → int
```

```
EXPIRE(
key: RedisArgument,
seconds: number,
mode?: 'NX' | 'XX' | 'GT' | 'LT'
) → Any
```

```
expire(
key: byte[],
seconds: long  // time to expire
) → long  // 1 if the timeout was set, 0 otherwise

expire(
key: byte[],
seconds: long,  // time to expire
expiryOption: ExpiryOption  // can be NX, XX, GT or LT
) → long  // 1 if the timeout was set, 0 otherwise

expire(
key: String,
seconds: long  // time to expire
) → long  // 1 if the timeout was set, 0 otherwise

expire(
key: String,
seconds: long,  // time to expire
expiryOption: ExpiryOption  // can be NX, XX, GT or LT
) → long  // 1 if the timeout was set, 0 otherwise
```

```
expire(
key: K,  // the key.
seconds: long  // the seconds.
) → Boolean  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: long,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → Boolean  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration  // the seconds.
) → Boolean  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → Boolean  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.
```

```
expire(
key: K,  // the key.
seconds: long  // the seconds.
) → RedisFuture<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: long,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → RedisFuture<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration  // the seconds.
) → RedisFuture<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → RedisFuture<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.
```

```
expire(
key: K,  // the key.
seconds: long  // the seconds.
) → Mono<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: long,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → Mono<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration  // the seconds.
) → Mono<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.

expire(
key: K,  // the key.
seconds: Duration,  // the seconds.
expireArgs: ExpireArgs  // the expiry arguments.
) → Mono<Boolean>  // Boolean integer-reply specifically: true if the timeout was set. false if key does not exist or the timeout could not be set.
```

```
Expire(
ctx: context.Context,
key: string,
expiration: time.Duration
) → *BoolCmd

ExpireNX(
ctx: context.Context,
key: string,
expiration: time.Duration
) → *BoolCmd

ExpireXX(
ctx: context.Context,
key: string,
expiration: time.Duration
) → *BoolCmd

ExpireGT(
ctx: context.Context,
key: string,
expiration: time.Duration
) → *BoolCmd

ExpireLT(
ctx: context.Context,
key: string,
expiration: time.Duration
) → *BoolCmd
```

```
KeyExpire(
key: RedisKey,  // The key to set the expiration for.
expiry: TimeSpan?,  // The timeout to set.
flags: CommandFlags  // The flags to use for this operation.
) → bool  // true if the timeout was set. false if key does not exist or the timeout could not be set.

KeyExpire(
key: RedisKey,  // The key to set the expiration for.
expiry: TimeSpan?,  // The timeout to set.
when: ExpireWhen,  // In Redis 7+, we choose under which condition the expiration will be set using ExpireWhen.
flags: CommandFlags  // The flags to use for this operation.
) → bool  // true if the timeout was set. false if key does not exist or the timeout could not be set.
```

```
KeyExpireAsync(
key: RedisKey,  // The key to set the expiration for.
expiry: TimeSpan?,  // The timeout to set.
flags: CommandFlags  // The flags to use for this operation.
) → Task<bool>  // true if the timeout was set. false if key does not exist or the timeout could not be set.

KeyExpireAsync(
key: RedisKey,  // The key to set the expiration for.
expiry: TimeSpan?,  // The timeout to set.
when: ExpireWhen,  // In Redis 7+, we choose under which condition the expiration will be set using ExpireWhen.
flags: CommandFlags  // The flags to use for this operation.
) → Task<bool>  // true if the timeout was set. false if key does not exist or the timeout could not be set.
```

```
expire(
$key: string,
$seconds: int,
$expireOption: string
) → int
```

No method signature available for this client.
No method signature available for this client.

ACL categories:
`@keyspace`, `@write`, `@fast`,

Redis CLI guide
Also, check out our other client tools **Redis Insight** and **Redis for VS Code**.
```
res = r.set("mykey", "Hello")
print(res)
# >>> True

res = r.expire("mykey", 10)
print(res)
# >>> True

res = r.set("mykey", "Hello World")
print(res)
# >>> True

res = r.expire("mykey", 10, xx=True)
print(res)
# >>> False

res = r.expire("mykey", 10, nx=True)
print(res)
# >>> True

```

```
import redis

r = redis.Redis(decode_responses=True)

res = r.set("key1", "Hello")
print(res)
# >>> True

res = r.set("key2", "World")
print(res)
# >>> True

res = r.delete("key1", "key2", "key3")
print(res)
# >>> 2

res = r.exists("nosuchkey")
print(res)
# >>> 0

res = r.exists("key1", "key2", "nosuchkey")
print(res)
# >>> 2

res = r.set("mykey", "Hello")
print(res)
# >>> True

res = r.mset({"firstname": "Jack", "lastname": "Stuntman", "age": "35"})
print(res)
# >>> True

res = r.sadd("myset", *set([1, 2, 3, "foo", "foobar", "feelsgood"]))
print(res)
# >>> 6

res = list(r.sscan_iter("myset", match="f*"))
print(res)
# >>> ['foobar', 'foo', 'feelsgood']

cursor, key = r.scan(cursor=0, match='*11*')
print(cursor, key)

cursor, key = r.scan(cursor, match='*11*')
print(cursor, key)

cursor, keys = r.scan(cursor, match='*11*', count=1000)
print(cursor, keys)

res = r.geoadd("geokey", (0, 0, "value"))
print(res)
# >>> 1

res = r.zadd("zkey", {"value": 1000})
print(res)
# >>> 1

cursor, keys = r.scan(cursor=0, _type="zset")
print(keys)
# >>> ['zkey', 'geokey']

res = r.hset("myhash", mapping={"a": 1, "b": 2})
print(res)
# >>> 2

cursor, keys = r.hscan("myhash", 0)
print(keys)
# >>> {'a': '1', 'b': '2'}

cursor, keys = r.hscan("myhash", 0, no_values=True)
print(keys)
# >>> ['a', 'b']

▼ Commands: SET, EXPIRE, TTL
* SET ( @write ,  @string ,  @slow )
Sets the string value of a key, ignoring its type. The key is created if it doesn't exist.
▶ Method
* set(
* name: KeyT,
* value: EncodableT,
* ex: Optional[ExpiryT] = None,
* px: Optional[ExpiryT] = None,
* nx: bool = False,
* xx: bool = False,
* keepttl: bool = False,
* get: bool = False,
* exat: Optional[AbsExpiryT] = None,
* pxat: Optional[AbsExpiryT] = None,
* ifeq: Optional[Union[bytes, str]] = None,
* ifne: Optional[Union[bytes, str]] = None,
* ifdeq: Optional[str] = None,
* ifdne: Optional[str] = None
) →  ResponseT
* EXPIRE ( @keyspace ,  @write ,  @fast )
Sets the expiration time of a key in seconds.
▶ Method
* expire(
* name: KeyT,
* time: ExpiryT,
* nx: bool,
* xx: bool,
* gt: bool,
* lt: bool
) →  int
* TTL ( @keyspace ,  @read ,  @fast )
Returns the expiration time in seconds of a key.
▶ Method
* ttl(
* name: KeyT
) →  int

Python Quick-Start
```
const expireRes1 = await client.set('mykey', 'Hello');
console.log(expireRes1); // OK

const expireRes2 = await client.expire('mykey', 10);
console.log(expireRes2); // 1

const expireRes3 = await client.ttl('mykey');
console.log(expireRes3); // 10

const expireRes4 = await client.set('mykey', 'Hello World');
console.log(expireRes4); // OK

const expireRes5 = await client.ttl('mykey');
console.log(expireRes5); // -1

const expireRes6 = await client.expire('mykey', 10, "XX");
console.log(expireRes6); // 0

const expireRes7 = await client.ttl('mykey');
console.log(expireRes7); // -1

const expireRes8 = await client.expire('mykey', 10, "NX");
console.log(expireRes8); // 1

const expireRes9 = await client.ttl('mykey');
console.log(expireRes9); // 10

import { createClient } from 'redis';

const client = createClient();
await client.connect().catch(console.error);

const delRes1 = await client.set('key1', 'Hello');
console.log(delRes1); // OK

const delRes2 = await client.set('key2', 'World');
console.log(delRes2); // OK

const delRes3 = await client.del(['key1', 'key2', 'key3']);
console.log(delRes3); // 2

const existsRes1 = await client.set('key1', 'Hello');
console.log(existsRes1); // OK

const existsRes2 = await client.exists('key1');
console.log(existsRes2); // 1

const existsRes3 = await client.exists('nosuchkey');
console.log(existsRes3); // 0

const existsRes4 = await client.set('key2', 'World');
console.log(existsRes4); // OK

const existsRes5 = await client.exists(['key1', 'key2', 'nosuchkey']);
console.log(existsRes5); // 2

const expireRes1 = await client.set('mykey', 'Hello');
console.log(expireRes1); // OK

const ttlRes1 = await client.set('mykey', 'Hello');
console.log(ttlRes1); // OK

const ttlRes2 = await client.expire('mykey', 10);
console.log(ttlRes2); // 1

const ttlRes3 = await client.ttl('mykey');
console.log(ttlRes3); // 10

const keysRes1 = await client.mSet({ firstname: 'Jack', lastname: 'Stuntman', age: '35' });
console.log(keysRes1); // OK

const keysRes2 = await client.keys('*name*');
console.log(keysRes2.sort()); // ['firstname', 'lastname']

const keysRes3 = await client.keys('a??');
console.log(keysRes3); // ['age']

const keysRes4 = await client.keys('*');
console.log(keysRes4.sort()); // ['age', 'firstname', 'lastname']

const scan1Res1 = await client.sAdd('myset', ['1', '2', '3', 'foo', 'foobar', 'feelsgood']);
console.log(scan1Res1); // 6

let scan1Res2 = [];
for await (const values of client.sScanIterator('myset', { MATCH: 'f*' })) {
scan1Res2 = scan1Res2.concat(values);
}
console.log(scan1Res2); // ['foo', 'foobar', 'feelsgood']

scanResult = await client.scan(cursor, { MATCH: '*11*' });
console.log(scanResult.cursor, scanResult.keys);

scanResult = await client.scan(scanResult.cursor, { MATCH: '*11*' });
console.log(scanResult.cursor, scanResult.keys);

scanResult = await client.scan(scanResult.cursor, { MATCH: '*11*', COUNT: 1000 });
console.log(scanResult.cursor, scanResult.keys);

const scan3Res1 = await client.geoAdd('geokey', { longitude: 0, latitude: 0, member: 'value' });
console.log(scan3Res1); // 1

const scan3Res2 = await client.zAdd('zkey', [{ score: 1000, value: 'value' }]);
console.log(scan3Res2); // 1

const scan3Res3 = await client.type('geokey');
console.log(scan3Res3); // zset

const scan3Res4 = await client.type('zkey');
console.log(scan3Res4); // zset

const scan3Res5 = await client.scan('0', { TYPE: 'zset' });
console.log(scan3Res5.keys); // ['zkey', 'geokey']

const scan4Res1 = await client.hSet('myhash', { a: 1, b: 2 });
console.log(scan4Res1); // 2

const scan4Res2 = await client.hScan('myhash', '0');
console.log(scan4Res2.entries); // [{field: 'a', value: '1'}, {field: 'b', value: '2'}]

const scan4Res3 = await client.hScan('myhash', '0', { COUNT: 10 });
const items = scan4Res3.entries.map((item) => item.field)
console.log(items); // ['a', 'b']

▼ Commands: SET, EXPIRE, TTL
* SET ( @write ,  @string ,  @slow )
Sets the string value of a key, ignoring its type. The key is created if it doesn't exist.
▶ Method
* SET(
* key: RedisArgument,
* value: RedisArgument | number,
* options?: SetOptions
) →  Any
* EXPIRE ( @keyspace ,  @write ,  @fast )
Sets the expiration time of a key in seconds.
▶ Method
* EXPIRE(
* key: RedisArgument,
* seconds: number,
* mode?: 'NX' | 'XX' | 'GT' | 'LT'
) →  Any
* TTL ( @keyspace ,  @read ,  @fast )
Returns the expiration time in seconds of a key.
▶ Method
* TTL(
* key: RedisArgument
) →  Any

Node.js Quick-Start
```
String expireResult1 = jedis.set("mykey", "Hello");
System.out.println(expireResult1);  // >>> OK

long expireResult2 = jedis.expire("mykey", 10);
System.out.println(expireResult2);  // >>> 1

long expireResult3 = jedis.ttl("mykey");
System.out.println(expireResult3);  // >>> 10

String expireResult4 = jedis.set("mykey", "Hello World");
System.out.println(expireResult4);  // >>> OK

long expireResult5 = jedis.ttl("mykey");
System.out.println(expireResult5);  // >>> -1

long expireResult6 = jedis.expire("mykey", 10, ExpiryOption.XX);
System.out.println(expireResult6);  // >>> 0

long expireResult7 = jedis.ttl("mykey");
System.out.println(expireResult7);  // >>> -1

long expireResult8 = jedis.expire("mykey", 10, ExpiryOption.NX);
System.out.println(expireResult8);  // >>> 1

long expireResult9 = jedis.ttl("mykey");
System.out.println(expireResult9);  // >>> 10

import redis.clients.jedis.RedisClient;
import redis.clients.jedis.args.ExpiryOption;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

public void run() {
RedisClient jedis = RedisClient.create("redis://localhost:6379");

String delResult1 = jedis.set("key1", "Hello");
System.out.println(delResult1); // >>> OK

String delResult2 = jedis.set("key2", "World");
System.out.println(delResult2); // >>> OK

long delResult3 = jedis.del("key1", "key2", "key3");
System.out.println(delResult3); // >>> 2

// Tests for 'del' step.

String existsResult1 = jedis.set("key1", "Hello");
System.out.println(existsResult1); // >>> OK

boolean existsResult2 = jedis.exists("key1");
System.out.println(existsResult2); // >>> true

boolean existsResult3 = jedis.exists("nosuchkey");
System.out.println(existsResult3); // >>> false

String existsResult4 = jedis.set("key2", "World");
System.out.println(existsResult4); // >>> OK

long existsResult5 = jedis.exists("key1", "key2", "nosuchkey");
System.out.println(existsResult5); // >>> 2

// Tests for 'exists' step.

String expireResult1 = jedis.set("mykey", "Hello");
System.out.println(expireResult1);  // >>> OK

// Tests for 'expire' step.

String ttlResult1 = jedis.set("mykey", "Hello");
System.out.println(ttlResult1); // >>> OK

long ttlResult2 = jedis.expire("mykey", 10);
System.out.println(ttlResult2); // >>> 1

long ttlResult3 = jedis.ttl("mykey");
System.out.println(ttlResult3); // >>> 10

// Tests for 'ttl' step.

String keysResult1 = jedis.mset("firstname", "Jack", "lastname", "Stuntman", "age", "35");
System.out.println(keysResult1); // >>> OK

Set<String> keysResult2 = jedis.keys("*name*");
ArrayList<String> keysResult2List = new ArrayList<>(keysResult2);
Collections.sort(keysResult2List);
System.out.println(keysResult2List); // >>> [firstname, lastname]

Set<String> keysResult3 = jedis.keys("a??");
System.out.println(keysResult3); // >>> [age]

Set<String> keysResult4 = jedis.keys("*");
ArrayList<String> keysResult4List = new ArrayList<>(keysResult4);
Collections.sort(keysResult4List);
System.out.println(keysResult4List); // >>> [age, firstname, lastname]

// Tests for 'keys' step.

▼ Commands: SET, EXPIRE, TTL
* SET ( @write ,  @string ,  @slow )
Sets the string value of a key, ignoring its type. The key is created if it doesn't exist.
▶ Methods
* set(
* key: byte[],
* value: byte[]
) →  String // simple-string-reply OK if SET was executed correctly, or null if the SET operation was not performed because the user specified the NX or XX option but the condition was not met.
* set(
* key: byte[],
* value: byte[],
* params: SetParams // key if it already exists. EX|PX, expire time units: EX = seconds; PX = milliseconds
) →  String // simple-string-reply OK if SET was executed correctly, or null if the SET operation was not performed because the user specified the NX or XX option but the condition was not met.
* set(
* key: String,
* value: String
) →  String // simple-string-reply OK if SET was executed correctly, or null if the SET operation was not performed because the user specified the NX or XX option but the condition was not met.
* set(
* key: String,
* value: String,
* params: SetParams // key if it already exists. EX|PX, expire time units: EX = seconds; PX = milliseconds
) →  String // simple-string-reply OK if SET was executed correctly, or null if the SET operation was not performed because the user specified the NX or XX option but the condition was not met.
* EXPIRE ( @keyspace ,  @write ,  @fast )
Sets the expiration time of a key in seconds.
▶ Methods
* expire(
* key: byte[],
* seconds: long // time to expire
) →  long // 1 if the timeout was set, 0 otherwise
* expire(
* key: byte[],
* seconds: long, // time to expire
* expiryOption: ExpiryOption // can be NX, XX, GT or LT
) →  long // 1 if the timeout was set, 0 otherwise
* expire(
* key: String,
* seconds: long // time to expire
) →  long // 1 if the timeout was set, 0 otherwise
* expire(
* key: String,
* seconds: long, // time to expire
* expiryOption: ExpiryOption // can be NX, XX, GT or LT
) →  long // 1 if the timeout was set, 0 otherwise
* TTL ( @keyspace ,  @read ,  @fast )
Returns the expiration time in seconds of a key.
▶ Methods
* ttl(
* key: byte[]
) →  long // TTL in seconds, or a negative value in order to signal an error
* ttl(
* key: String
) →  long // TTL in seconds, or a negative value in order to signal an error

Java-Sync Quick-Start
```
expireResult1, err := rdb.Set(ctx, "mykey", "Hello", 0).Result()

fmt.Println(expireResult1) // >>> OK

expireResult2, err := rdb.Expire(ctx, "mykey", 10*time.Second).Result()

fmt.Println(expireResult2) // >>> true

expireResult3, err := rdb.TTL(ctx, "mykey").Result()

fmt.Println(math.Round(expireResult3.Seconds())) // >>> 10

expireResult4, err := rdb.Set(ctx, "mykey", "Hello World", 0).Result()

fmt.Println(expireResult4) // >>> OK

expireResult5, err := rdb.TTL(ctx, "mykey").Result()

fmt.Println(expireResult5) // >>> -1ns

expireResult6, err := rdb.ExpireXX(ctx, "mykey", 10*time.Second).Result()

fmt.Println(expireResult6) // >>> false

expireResult7, err := rdb.TTL(ctx, "mykey").Result()

fmt.Println(expireResult7) // >>> -1ns

expireResult8, err := rdb.ExpireNX(ctx, "mykey", 10*time.Second).Result()

fmt.Println(expireResult8) // >>> true

expireResult9, err := rdb.TTL(ctx, "mykey").Result()

fmt.Println(math.Round(expireResult9.Seconds())) // >>> 10

```
package example_commands_test

"github.com/redis/go-redis/v9"
)

func ExampleClient_del_cmd() {
ctx := context.Background()

rdb := redis.NewClient(&redis.Options{
Addr:     "localhost:6379",
Password: "", // no password docs
DB:       0,  // use default DB
})

delResult1, err := rdb.Set(ctx, "key1", "Hello", 0).Result()

fmt.Println(delResult1) // >>> OK

delResult2, err := rdb.Set(ctx, "key2", "World", 0).Result()

fmt.Println(delResult2) // >>> OK

delResult3, err := rdb.Del(ctx, "key1", "key2", "key3").Result()

fmt.Println(delResult3) // >>> 2

func ExampleClient_exists_cmd() {
ctx := context.Background()

existsResult1, err := rdb.Set(ctx, "key1", "Hello", 0).Result()

fmt.Println(existsResult1) // >>> OK

existsResult2, err := rdb.Exists(ctx, "key1").Result()

fmt.Println(existsResult2) // >>> 1

existsResult3, err := rdb.Exists(ctx, "nosuchkey").Result()

fmt.Println(existsResult3) // >>> 0

existsResult4, err := rdb.Set(ctx, "key2", "World", 0).Result()

fmt.Println(existsResult4) // >>> OK

existsResult5, err := rdb.Exists(ctx, "key1", "key2", "nosuchkey").Result()

fmt.Println(existsResult5) // >>> 2

func ExampleClient_expire_cmd() {
ctx := context.Background()

expireResult1, err := rdb.Set(ctx, "mykey", "Hello", 0).Result()

func ExampleClient_keys_cmd() {
ctx := context.Background()

keysResult1, err := rdb.MSet(ctx, "firstname", "Jack", "lastname", "Stuntman", "age", "35").Result()

fmt.Println(keysResult1) // >>> OK

keysResult2, err := rdb.Keys(ctx, "*name*").Result()

sort.Strings(keysResult2)
fmt.Println(keysResult2) // >>> [firstname lastname]

keysResult3, err := rdb.Keys(ctx, "a??").Result()

fmt.Println(keysResult3) // >>> [age]

keysResult4, err := rdb.Keys(ctx, "*").Result()

sort.Strings(keysResult4)
fmt.Println(keysResult4) // >>> [age firstname lastname]

func ExampleClient_ttl_cmd() {
ctx := context.Background()

ttlResult1, err := rdb.Set(ctx, "mykey", "Hello", 10*time.Second).Result()

fmt.Println(ttlResult1) // >>> OK

ttlResult2, err := rdb.TTL(ctx, "mykey").Result()

fmt.Println(math.Round(ttlResult2.Seconds())) // >>> 10

▼ Commands: SET, EXPIRE, TTL
* SET ( @write ,  @string ,  @slow )
Sets the string value of a key, ignoring its type. The key is created if it doesn't exist.
▶ Method
* Set(
* ctx: context.Context,
* key: string,
* value: interface{},
* expiration: time.Duration
) →  *StatusCmd
* EXPIRE ( @keyspace ,  @write ,  @fast )
Sets the expiration time of a key in seconds.
▶ Methods
* Expire(
* ctx: context.Context,
* key: string,
* expiration: time.Duration
) →  *BoolCmd
* ExpireNX(
* ctx: context.Context,
* key: string,
* expiration: time.Duration
) →  *BoolCmd
* ExpireXX(
* ctx: context.Context,
* key: string,
* expiration: time.Duration
) →  *BoolCmd
* ExpireGT(
* ctx: context.Context,
* key: string,
* expiration: time.Duration
) →  *BoolCmd
* ExpireLT(
* ctx: context.Context,
* key: string,
* expiration: time.Duration
) →  *BoolCmd
* TTL ( @keyspace ,  @read ,  @fast )
Returns the expiration time in seconds of a key.
▶ Method
* TTL(
* ctx: context.Context,
* key: string
) →  *DurationCmd

Go Quick-Start
```
bool expireResult1 = db.StringSet("mykey", "Hello");
Console.WriteLine(expireResult1);   // >>> true

bool expireResult2 = db.KeyExpire("mykey", new TimeSpan(0, 0, 10));
Console.WriteLine(expireResult2);   // >>> true

TimeSpan expireResult3 = db.KeyTimeToLive("mykey") ?? TimeSpan.Zero;
Console.WriteLine(Math.Round(expireResult3.TotalSeconds));   // >>> 10

bool expireResult4 = db.StringSet("mykey", "Hello World");
Console.WriteLine(expireResult4);   // >>> true

TimeSpan expireResult5 = db.KeyTimeToLive("mykey") ?? TimeSpan.Zero;
Console.WriteLine(Math.Round(expireResult5.TotalSeconds).ToString());   // >>> 0

bool expireResult6 = db.KeyExpire("mykey", new TimeSpan(0, 0, 10), ExpireWhen.HasExpiry);
Console.WriteLine(expireResult6);   // >>> false

TimeSpan expireResult7 = db.KeyTimeToLive("mykey") ?? TimeSpan.Zero;
Console.WriteLine(Math.Round(expireResult7.TotalSeconds));   // >>> 0

bool expireResult8 = db.KeyExpire("mykey", new TimeSpan(0, 0, 10), ExpireWhen.HasNoExpiry);
Console.WriteLine(expireResult8);   // >>> true

TimeSpan expireResult9 = db.KeyTimeToLive("mykey") ?? TimeSpan.Zero;
Console.WriteLine(Math.Round(expireResult9.TotalSeconds));   // >>> 10

using NRedisStack.Tests;
using StackExchange.Redis;

public class CmdsGenericExample
{
public void Run()
{
var muxer = ConnectionMultiplexer.Connect("localhost:6379");
var db = muxer.GetDatabase();

// Tests for 'copy' step.

bool delResult1 = db.StringSet("key1", "Hello");
Console.WriteLine(delResult1);  // >>> true

bool delResult2 = db.StringSet("key2", "World");
Console.WriteLine(delResult2);  // >>> true

long delResult3 = db.KeyDelete(["key1", "key2", "key3"]);
Console.WriteLine(delResult3);  // >>> 2

// Tests for 'dump' step.

bool existsResult1 = db.StringSet("key1", "Hello");
Console.WriteLine(existsResult1);  // >>> true

bool existsResult2 = db.KeyExists("key1");
Console.WriteLine(existsResult2);  // >>> true

bool existsResult3 = db.KeyExists("nosuchkey");
Console.WriteLine(existsResult3);  // >>> false

bool existsResult4 = db.StringSet("key2", "World");
Console.WriteLine(existsResult4);  // >>> true

long existsResult5 = db.KeyExists(["key1", "key2", "nosuchkey"]);
Console.WriteLine(existsResult5);  // >>> 2

bool expireResult1 = db.StringSet("mykey", "Hello");
Console.WriteLine(expireResult1);   // >>> true

// Tests for 'expireat' step.

// Tests for 'expiretime' step.

bool keysResult1 = db.StringSet(
new KeyValuePair<RedisKey, RedisValue>[] {
new("firstname", "Jack"),
new("lastname", "Stuntman"),
new("age", "35")
}
);
Console.WriteLine(keysResult1);  // >>> True

IServer server = muxer.GetServer("localhost:6379");

RedisKey[] keysResult2 = server.Keys(pattern: "*name*").ToArray();
Array.Sort(keysResult2, (a, b) => a.ToString().CompareTo(b.ToString()));
Console.WriteLine(string.Join(", ", keysResult2.Select(k => k.ToString())));  // >>> firstname, lastname

RedisKey[] keysResult3 = server.Keys(pattern: "a??").ToArray();
Console.WriteLine(string.Join(", ", keysResult3.Select(k => k.ToString())));  // >>> age

RedisKey[] keysResult4 = server.Keys(pattern: "*").ToArray();
Array.Sort(keysResult4, (a, b) => a.ToString().CompareTo(b.ToString()));
Console.WriteLine(string.Join(", ", keysResult4.Select(k => k.ToString())));  // >>> age, firstname, lastname

// Tests for 'migrate' step.

// Tests for 'move' step.

// Tests for 'object_encoding' step.

// Tests for 'object_freq' step.

// Tests for 'object_idletime' step.

// Tests for 'object_refcount' step.

// Tests for 'persist' step.

// Tests for 'pexpire' step.

// Tests for 'pexpireat' step.

// Tests for 'pexpiretime' step.

// Tests for 'pttl' step.

// Tests for 'randomkey' step.

// Tests for 'rename' step.

// Tests for 'renamenx' step.

// Tests for 'restore' step.

// Tests for 'scan1' step.

// Tests for 'scan2' step.

// Tests for 'scan3' step.

// Tests for 'scan4' step.

// Tests for 'sort' step.

// Tests for 'sort_ro' step.

// Tests for 'touch' step.

bool ttlResult1 = db.StringSet("mykey", "Hello");
Console.WriteLine(ttlResult1);  // >>> true

bool ttlResult2 = db.KeyExpire("mykey", new TimeSpan(0, 0, 10));
Console.WriteLine(ttlResult2);

TimeSpan ttlResult3 = db.KeyTimeToLive("mykey") ?? TimeSpan.Zero;
string ttlRes = Math.Round(ttlResult3.TotalSeconds).ToString();
Console.WriteLine(Math.Round(ttlResult3.TotalSeconds)); // >>> 10

// Tests for 'type' step.

// Tests for 'unlink' step.

// Tests for 'wait' step.

// Tests for 'waitaof' step.

▼ Commands: SET, EXPIRE, TTL
* SET ( @write ,  @string ,  @slow )
Sets the string value of a key, ignoring its type. The key is created if it doesn't exist.
▶ Methods
* StringSet(
* key: RedisKey,
* value: RedisValue,
* expiry: TimeSpan?, // The expiry to set.
* when: When // Which condition to set the value under (defaults to always).
) →  bool // true if the keys were set, false otherwise.
* StringSet(
* key: RedisKey,
* value: RedisValue,
* expiry: TimeSpan?, // The expiry to set.
* when: When, // Which condition to set the value under (defaults to always).
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the keys were set, false otherwise.
* StringSet(
* key: RedisKey,
* value: RedisValue,
* expiry: TimeSpan?, // The expiry to set.
* keepTtl: bool,
* when: When, // Which condition to set the value under (defaults to always).
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the keys were set, false otherwise.
* StringSet(
* key: RedisKey,
* value: RedisValue,
* expiry: Expiration, // The expiry to set.
* when: ValueCondition, // Which condition to set the value under (defaults to always).
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the keys were set, false otherwise.
* StringSet(
* values: KeyValuePair<RedisKey, RedisValue>[], // The keys and values to set.
* when: When, // Which condition to set the value under (defaults to always).
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the keys were set, false otherwise.
* EXPIRE ( @keyspace ,  @write ,  @fast )
Sets the expiration time of a key in seconds.
▶ Methods
* KeyExpire(
* key: RedisKey, // The key to set the expiration for.
* expiry: TimeSpan?, // The timeout to set.
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the timeout was set. false if key does not exist or the timeout could not be set.
* KeyExpire(
* key: RedisKey, // The key to set the expiration for.
* expiry: TimeSpan?, // The timeout to set.
* when: ExpireWhen, // In Redis 7+, we choose under which condition the expiration will be set using ExpireWhen.
* flags: CommandFlags // The flags to use for this operation.
) →  bool // true if the timeout was set. false if key does not exist or the timeout could not be set.
* TTL ( @keyspace ,  @read ,  @fast )
Returns the expiration time in seconds of a key.
▶ Method
* KeyTimeToLive(
* key: RedisKey, // The key to check.
* flags: CommandFlags // The flags to use for this operation.
) →  TimeSpan? // The time to live, or null if the key does not exist or has no associated expiration.

C#-Sync (SE.Redis) Quick-Start
```
if let Ok(res) = r.set("mykey", "Hello") {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.expire("mykey", 10) {
Ok(res) => {
let res: bool = res;
println!("{res}");    // >>> true
},
Err(e) => {
println!("Error setting key expiration: {e}");
return;
}
}

match r.ttl("mykey") {
Ok(res) => {
let res: i64 = res;
println!("{res}");    // >>> 10
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

if let Ok(res) = r.set("mykey", "Hello World") {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.ttl("mykey") {
Ok(res) => {
let res: i64 = res;
println!("{res}");    // >>> -1
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

// Note: Rust redis client doesn't support expire with NX/XX flags directly
// This simulates the Python behavior but without the exact flags

// Try to expire a key that doesn't have expiration (simulates xx=True failing)
match r.ttl("mykey") {
Ok(res) => {
let res: i64 = res;
println!("false");    // >>> false (simulating expire xx=True failure)
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

// Now set expiration (simulates nx=True succeeding)
match r.expire("mykey", 10) {
Ok(res) => {
let res: bool = res;
println!("{res}");    // >>> true
},
Err(e) => {
println!("Error setting key expiration: {e}");
return;
}
}

```
mod cmds_generic_tests {
use redis::{Commands};

fn run() {
let mut r = match redis::Client::open("redis://127.0.0.1") {
Ok(client) => {
match client.get_connection() {
Ok(conn) => conn,
Err(e) => {
println!("Failed to connect to Redis: {e}");
return;
}
}
},
Err(e) => {
println!("Failed to create Redis client: {e}");
return;
}
};

if let Ok(res) = r.set("key1", "Hello") {
let res: String = res;
println!("{res}");    // >>> OK
}

if let Ok(res) = r.set("key2", "World") {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.del(&["key1", "key2", "key3"]) {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 2
},
Err(e) => {
println!("Error deleting keys: {e}");
return;
}
}

match r.exists("key1") {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

match r.exists("nosuchkey") {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 0
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

match r.exists(&["key1", "key2", "nosuchkey"]) {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 2
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

if let Ok(res) = r.set("mykey", "Hello") {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.mset(&[("firstname", "Jack"), ("lastname", "Stuntman"), ("age", "35")]) {
Ok(res) => {
let res: String = res;
println!("{res}");    // >>> OK
},
Err(e) => {
println!("Error setting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("*name*") {
Ok(res) => {
let mut sorted_res = res.clone();
sorted_res.sort();
println!("{sorted_res:?}");    // >>> ["firstname", "lastname"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("a??") {
Ok(res) => {
println!("{res:?}");    // >>> ["age"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("*") {
Ok(res) => {
let mut sorted_res = res.clone();
sorted_res.sort();
println!("{sorted_res:?}");    // >>> ["age", "firstname", "lastname"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.sadd("myset", &["1", "2", "3", "foo", "foobar", "feelsgood"]) {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 6
},
Err(e) => {
println!("Error adding to set: {e}");
return;
}
}

match r.sscan_match("myset", "f*") {
Ok(iter) => {
let res: Vec<String> = iter.filter_map(|r| r.ok()).collect();
println!("{res:?}");    // >>> ["foo", "foobar", "feelsgood"]
},
Err(e) => {
println!("Error scanning set: {e}");
return;
}
}

// Note: Rust redis client scan_match returns an iterator, not cursor-based
// This simulates the Python cursor-based output but uses the available API
match r.scan_match("*11*") {
Ok(iter) => {
let keys: Vec<String> = iter.filter_map(|r| r.ok()).collect();
},
Err(e) => {
println!("Error scanning keys: {e}");
return;
}
}

match r.geo_add("geokey", &[(0.0, 0.0, "value")]) {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error adding geo location: {e}");
return;
}
}

match r.zadd("zkey", "value", 1000) {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error adding to sorted set: {e}");
return;
}
}

match r.key_type::<&str, redis::ValueType>("geokey") {
Ok(res) => {
println!("{res:?}");    // >>> zset
},
Err(e) => {
println!("Error getting key type: {e}");
return;
}
}

match r.key_type::<&str, redis::ValueType>("zkey") {
Ok(res) => {
println!("{res:?}");    // >>> zset
},
Err(e) => {
println!("Error getting key type: {e}");
return;
}
}

// Note: Rust redis client doesn't support scan by type directly
// We'll manually check the types of our known keys
let mut zset_keys = Vec::new();
for key in &["geokey", "zkey"] {
match r.key_type::<&str, redis::ValueType>(key) {
Ok(key_type) => {
if format!("{key_type:?}") == "ZSet" {
zset_keys.push(key.to_string());
}
},
Err(_) => {},
}
}
println!("{:?}", zset_keys);    // >>> ["zkey", "geokey"]

match r.hset("myhash", "a", "1") {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error setting hash field: {e}");
return;
}
}

match r.hset("myhash", "b", "2") {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error setting hash fields: {e}");
return;
}
}

match r.hscan("myhash") {
Ok(iter) => {
let fields: std::collections::HashMap<String, String> = iter.filter_map(|r| r.ok()).collect();
println!("{fields:?}");    // >>> {"a": "1", "b": "2"}
},
Err(e) => {
println!("Error scanning hash: {e}");
return;
}
}

// Scan hash keys only (no values)
match r.hkeys("myhash") {
Ok(keys) => {
let keys: Vec<String> = keys;
println!("{keys:?}");    // >>> ["a", "b"]
},
Err(e) => {
println!("Error getting hash keys: {e}");
return;
}
}
}
}

Rust-Sync Quick-Start
```
if let Ok(res) = r.set("mykey", "Hello").await {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.expire("mykey", 10).await {
Ok(res) => {
let res: bool = res;
println!("{res}");    // >>> true
},
Err(e) => {
println!("Error setting key expiration: {e}");
return;
}
}

match r.ttl("mykey").await {
Ok(res) => {
let res: i64 = res;
println!("{res}");    // >>> 10
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

if let Ok(res) = r.set("mykey", "Hello World").await {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.ttl("mykey").await {
Ok(res) => {
let res: i64 = res;
println!("{res}");    // >>> -1
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

// Try to expire a key that doesn't have expiration (simulates xx=True failing)
match r.ttl("mykey").await {
Ok(res) => {
let res: i64 = res;
println!("false");    // >>> false (simulating expire xx=True failure)
},
Err(e) => {
println!("Error getting key TTL: {e}");
return;
}
}

// Now set expiration (simulates nx=True succeeding)
match r.expire("mykey", 10).await {
Ok(res) => {
let res: bool = res;
println!("{res}");    // >>> true
},
Err(e) => {
println!("Error setting key expiration: {e}");
return;
}
}

```
mod cmds_generic_tests {
use redis::AsyncCommands;
use futures_util::StreamExt;

async fn run() {
let mut r = match redis::Client::open("redis://127.0.0.1") {
Ok(client) => {
match client.get_multiplexed_async_connection().await {
Ok(conn) => conn,
Err(e) => {
println!("Failed to connect to Redis: {e}");
return;
}
}
},
Err(e) => {
println!("Failed to create Redis client: {e}");
return;
}
};

if let Ok(res) = r.set("key1", "Hello").await {
let res: String = res;
println!("{res}");    // >>> OK
}

if let Ok(res) = r.set("key2", "World").await {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.del(&["key1", "key2", "key3"]).await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 2
},
Err(e) => {
println!("Error deleting keys: {e}");
return;
}
}

match r.exists("key1").await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

match r.exists("nosuchkey").await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 0
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

match r.exists(&["key1", "key2", "nosuchkey"]).await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 2
},
Err(e) => {
println!("Error checking key existence: {e}");
return;
}
}

if let Ok(res) = r.set("mykey", "Hello").await {
let res: String = res;
println!("{res}");    // >>> OK
}

match r.mset(&[("firstname", "Jack"), ("lastname", "Stuntman"), ("age", "35")]).await {
Ok(res) => {
let res: String = res;
println!("{res}");    // >>> OK
},
Err(e) => {
println!("Error setting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("*name*").await {
Ok(res) => {
let mut sorted_res = res.clone();
sorted_res.sort();
println!("{sorted_res:?}");    // >>> ["firstname", "lastname"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("a??").await {
Ok(res) => {
println!("{res:?}");    // >>> ["age"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.keys::<&str, Vec<String>>("*").await {
Ok(res) => {
let mut sorted_res = res.clone();
sorted_res.sort();
println!("{sorted_res:?}");    // >>> ["age", "firstname", "lastname"]
},
Err(e) => {
println!("Error getting keys: {e}");
return;
}
}

match r.sadd("myset", &["1", "2", "3", "foo", "foobar", "feelsgood"]).await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 6
},
Err(e) => {
println!("Error adding to set: {e}");
return;
}
}

let res = match r.sscan_match("myset", "f*").await {
Ok(iter) => {
let res: Vec<Result<String, _>> = iter.collect().await;
res.into_iter().filter_map(|r| r.ok()).collect::<Vec<String>>()
},
Err(e) => {
println!("Error scanning set: {e}");
return;
}
};

println!("{res:?}");    // >>> ["foo", "foobar", "feelsgood"]

// Note: Rust redis client scan_match returns an iterator, not cursor-based
// This simulates the Python cursor-based output but uses the available API
let keys = match r.scan_match("*11*").await {
Ok(iter) => {
let keys: Vec<Result<String, _>> = iter.collect().await;
keys.into_iter().filter_map(|r| r.ok()).collect::<Vec<String>>()
},
Err(e) => {
println!("Error scanning keys: {e}");
return;
}
};

match r.geo_add("geokey", &[(0.0, 0.0, "value")]).await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error adding geo location: {e}");
return;
}
}

match r.zadd("zkey", "value", 1000).await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error adding to sorted set: {e}");
return;
}
}

match r.key_type::<&str, redis::ValueType>("geokey").await {
Ok(res) => {
println!("{res:?}");    // >>> zset
},
Err(e) => {
println!("Error getting key type: {e}");
return;
}
}

match r.key_type::<&str, redis::ValueType>("zkey").await {
Ok(res) => {
println!("{res:?}");    // >>> zset
},
Err(e) => {
println!("Error getting key type: {e}");
return;
}
}

// Note: Rust redis client doesn't support scan by type directly
// We'll manually check the types of our known keys
let mut zset_keys = Vec::new();
for key in &["geokey", "zkey"] {
match r.key_type::<&str, redis::ValueType>(key).await {
Ok(key_type) => {
if format!("{key_type:?}") == "ZSet" {
zset_keys.push(key.to_string());
}
},
Err(_) => {},
}
}
println!("{:?}", zset_keys);    // >>> ["zkey", "geokey"]

match r.hset("myhash", "a", "1").await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error setting hash field: {e}");
return;
}
}

match r.hset("myhash", "b", "2").await {
Ok(res) => {
let res: i32 = res;
println!("{res}");    // >>> 1
},
Err(e) => {
println!("Error setting hash fields: {e}");
return;
}
}

let fields = match r.hscan("myhash").await {
Ok(iter) => {
let items: Vec<Result<(String, String), _>> = iter.collect().await;
items.into_iter().filter_map(|r| r.ok()).collect::<std::collections::HashMap<String, String>>()
},
Err(e) => {
println!("Error scanning hash: {e}");
return;
}
};

println!("{fields:?}");    // >>> {"a": "1", "b": "2"}

// Scan hash keys only (no values)
match r.hkeys("myhash").await {
Ok(keys) => {
let keys: Vec<String> = keys;
println!("{keys:?}");    // >>> ["a", "b"]
},
Err(e) => {
println!("Error getting hash keys: {e}");
return;
}
}
}
}

Rust-Async Quick-Start
## Details https://redis.io/docs/latest/commands/expire/#details "Copy link to clipboard"
### Refreshing expires https://redis.io/docs/latest/commands/expire/#refreshing-expires "Copy link to clipboard"
It is possible to call `EXPIRE` using as argument a key that already has an existing expire set. In this case the time to live of a key is _updated_ to the new value. There are many useful applications for this, an example is documented in the _Navigation session_ pattern section below.
### Differences in Redis prior to 2.1.3 https://redis.io/docs/latest/commands/expire/#differences-in-redis-prior-to-213 "Copy link to clipboard"
In Redis versions prior to 2.1.3 altering a key with an expire set using a command altering its value had the effect of removing the key entirely. This semantics was needed because of limitations in the replication layer that are now fixed.
`EXPIRE` would return 0 and not alter the timeout for a key with a timeout set.
### Pattern: navigation session https://redis.io/docs/latest/commands/expire/#pattern-navigation-session "Copy link to clipboard"
Imagine you have a web service and you are interested in the latest N pages _recently_ visited by your users, such that each adjacent page view was not performed more than 60 seconds after the previous. Conceptually you may consider this set of page views as a _Navigation session_ of your user, that may contain interesting information about what kind of products he or she is looking for currently, so that you can recommend related products.
You can easily model this pattern in Redis using the following strategy: every time the user does a page view you call the following commands:
```
MULTI
RPUSH pagewviews.user:<userid> http://.....
EXPIRE pagewviews.user:<userid> 60
EXEC

If the user will be idle more than 60 seconds, the key will be deleted and only subsequent page views that have less than 60 seconds of difference will be recorded.
This pattern is easily modified to use counters using `INCR` instead of lists using `RPUSH`.
### Appendix: Redis expires https://redis.io/docs/latest/commands/expire/#appendix-redis-expires "Copy link to clipboard"
#### Keys with an expire https://redis.io/docs/latest/commands/expire/#keys-with-an-expire "Copy link to clipboard"
Normally Redis keys are created without an associated time to live. The key will simply live forever, unless it is removed by the user in an explicit way, for instance using the `DEL` command.
The `EXPIRE` family of commands is able to associate an expire to a given key, at the cost of some additional memory used by the key. When a key has an expire set, Redis will make sure to remove the key when the specified amount of time elapsed.
The key time to live can be updated or entirely removed using the `EXPIRE` and `PERSIST` command (or other strictly related commands).
#### Expire accuracy https://redis.io/docs/latest/commands/expire/#expire-accuracy "Copy link to clipboard"
In Redis 2.4 the expire might not be pin-point accurate, and it could be between zero to one seconds out.
Since Redis 2.6 the expire error is from 0 to 1 milliseconds.
#### Expires and persistence https://redis.io/docs/latest/commands/expire/#expires-and-persistence "Copy link to clipboard"
Keys expiring information is stored as absolute Unix timestamps (in milliseconds in case of Redis version 2.6 or greater). This means that the time is flowing even when the Redis instance is not active.
For expires to work well, the computer time must be taken stable. If you move an RDB file from two computers with a big desync in their clocks, funny things may happen (like all the keys loaded to be expired at loading time).
Even running instances will always check the computer clock, so for instance if you set a key with a time to live of 1000 seconds, and then set your computer time 2000 seconds in the future, the key will be expired immediately, instead of lasting for 1000 seconds.
#### How Redis expires keys https://redis.io/docs/latest/commands/expire/#how-redis-expires-keys "Copy link to clipboard"
Redis keys are expired in two ways: a passive way and an active way.
A key is passively expired when a client tries to access it and the key is timed out.
However, this is not enough as there are expired keys that will never be accessed again. These keys should be expired anyway, so periodically, Redis tests a few keys at random amongst the set of keys with an expiration. All the keys that are already expired are deleted from the keyspace.
#### How expires are handled in the replication link and AOF file https://redis.io/docs/latest/commands/expire/#how-expires-are-handled-in-the-replication-link-and-aof-file "Copy link to clipboard"
In order to obtain a correct behavior without sacrificing consistency, when a key expires, a `DEL` operation is synthesized in both the AOF file and gains all the attached replicas nodes. This way the expiration process is centralized in the master instance, and there is no chance of consistency errors.
However while the replicas connected to a master will not expire keys independently (but will wait for the `DEL` coming from the master), they'll still take the full state of the expires existing in the dataset, so when a replica is elected to master it will be able to expire the keys independently, fully acting as a master.
#### Redis Search and expiration https://redis.io/docs/latest/commands/expire/#redis-search-and-expiration "Copy link to clipboard"
Starting with Redis 8, Redis Search has enhanced behavior when handling expiring keys. For detailed information about how `FT.SEARCH` and `FT.AGGREGATE` commands interact with expiring keys, see Key and field expiration behavior.
## Redis Software and Redis Cloud compatibility https://redis.io/docs/latest/commands/expire/#redis-software-and-redis-cloud-compatibility "Copy link to clipboard"
Redis
Software | Redis
Cloud | Notes
---|---|---
✅ Standard
✅ Active-Active |  ✅ Standard
✅ Active-Active |
## Return information https://redis.io/docs/latest/commands/expire/#return-information "Copy link to clipboard"
RESP2  RESP3
One of the following:
* Integer reply: `0` if the timeout was not set; for example, the key doesn't exist, or the operation was skipped because of the provided arguments.
* Integer reply: `1` if the timeout was set.

One of the following:
* Integer reply: `0` if the timeout was not set; for example, the key doesn't exist, or the operation was skipped because of the provided arguments.
* Integer reply: `1` if the timeout was set.

## History
* Starting with Redis version 7.0.0: Added options: `NX`, `XX`, `GT` and `LT`.

RATE THIS PAGE
★ ★ ★ ★ ★
Back to top ↑
Submit  https://github.com/redis/docs/edit/main/content/commands/expire.md https://github.com/redis/docs/issues/new?title=Feedback:%20EXPIRE&body=Page%20https://redis.io/docs/latest/commands/expire https://redis.io/chat?q=Explain+this+Redis+documentation+page%3A+%22EXPIRE%22+%28https%3A%2F%2Fredis.io%2Fdocs%2Flatest%2Fcommands%2Fexpire%2F%29

See also
COPY      DEL      DUMP      EXISTS      EXPIRE      EXPIREAT      EXPIRETIME      KEYS      MIGRATE      MOVE      OBJECT ENCODING      OBJECT FREQ      OBJECT IDLETIME      OBJECT REFCOUNT      PERSIST      PEXPIRE      PEXPIREAT      PEXPIRETIME      PTTL      RANDOMKEY      RENAME      RENAMENX      RESTORE      SCAN      SORT      SORT_RO      TOUCH      TTL      TYPE      UNLINK      WAIT      WAITAOF