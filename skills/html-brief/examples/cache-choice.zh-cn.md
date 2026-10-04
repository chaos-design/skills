---
title: 缓存选型评审
subtitle: Redis 与 Memcached 在本服务的取舍
theme: document
mode: auto
---

## 结论

> key: 选 Redis。读写量由持久化副本与过期语义主导，Memcached 的多线程简单模型不再是最短路径。

```kv
场景 | 会话缓存、计数、排行榜锁
读写比 | 写占三成，且不可丢
过期语义 | 需要按业务键设置不同 TTL
运维现状 | 已有一套 Redis 副本与告警
```

## 取舍对照 {span=2}

| 维度 | Redis | Memcached |
| --- | --- | --- |
| 数据结构 | 支持 | 不支持 |
| 持久化 | 支持 | 不支持 |
| 按键过期 | 支持 | 支持 |
| 简单读取性能 | warn | ok |
| 运维复杂度 | warn | ok |

## 请求路径 {span=2}

```flow LR
(API) -> Redis: GET key
Redis -> [(Replica)]: read
Redis --> API: hit
Redis -.-> API: miss
API -> [(MySQL)]: query
API -> Redis: SETEX 300
```

## 容量与风险 {span=2}

```limits
内存水位 | 3.1 GiB of 4 GiB | 78% | 含会话与热榜
单键 TTL 上限 | 24h | 60% | 排行榜需要长 TTL
写放大 | 3.4x | 35% | AOF everysec 计入
```

```stat
命中率 | 94% | -2% | warn
p99 读取 | 1.8ms | +0.3ms | warn
副本延迟 | 0.4ms | 稳定 | good
```

## 迁移步骤

1. 建立按业务键分组的 TTL 清单。
2. 在预发环境打开 `maxmemory-policy noeviction`。
3. 灰度 10% 流量，观察命中率与 p99 读取。
4. 全量后删除旧的 Memcached 实例，保留一周回滚窗口。

> warn: 关闭 volatile-lru 之前先确认所有键都带 TTL。
> 否则会退化为 noeviction，并把写入打满。

## 需要补充的信息

- 峰值 QPS 与键平均大小。
- 是否需要跨可用区的写入。
- 现有 Memcached 集群的退役时间窗口。