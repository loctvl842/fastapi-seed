# fastapi-seed

## Pre-requisites

- Python 3.11.3
- Linter: **Ruff**
- Formatter: **Black**

## Usage

### Print help

```bash
make
```

### Run the application

```bash
make run
```

#### Using docker-compose

```bash
docker-compose -f ./docker/docker-compose.yml up
```

For development, recommend using one local database between multiple projects.
Before running the application, make sure the volumes are created.

- Volume for Postgres

```bash
docker volume create pgdata
```

- Volume for Redis

```bash
docker volume create redisdata
```

### Database

- Generate new migration file

```bash
make generate-migration
```

- Checkout the migration history

```bash
alembic history
```

- Upgrade to the latest revision

```bash
make upgrade
```

- Downgrade to a specific revision

```bash
alembic downgrade <revision>
```

Or downgrade to the previous revision

```bash
make rollback
```

#### Transaction

Easy using transaction with `Transactional` decorator

```python
from core.db import Transactional

class NewsController(BaseController[News]):
  @Transactional()
  async def seed(self):
    ...
```

### Cache

#### Using decorator

```python
from core.cache import Cache

@Cache.cached(prefix="user", ttl=30 * 24 * 60 * 60)
async foo() {

}
```

#### Using `attempt` method

```python
from core.cache import Cache

@Cache.cached(prefix="user", ttl=30 * 24 * 60 * 60)

async def scrape(url: str) {
  return await fetch(url)
}

async def main() {
  data = await Cache.attempt(
    key="linkedin-scraper",
    ttl=60,
    fn=scrape_linkedin,
    url="https://www.linkedin.com/"
  )
}
```

### Code quality

- **Check format the code**

```bash
make check-format
```

- **Lint the code**

```bash
make lint
```
