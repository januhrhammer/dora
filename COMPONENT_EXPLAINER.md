# Component Explainer - Learning FastAPI and Svelte

This document explains each component in detail to help you learn FastAPI and Svelte.

---

## Backend Components (FastAPI)

### 1. database.py - Database Connection

**What it does**: Sets up the connection to SQLite database and provides sessions.

**Key concepts**:

```python
engine = create_engine(SQLALCHEMY_DATABASE_URL)
```
- **Engine**: The core interface to the database. It manages connections.
- **SQLite**: A simple file-based database (stores everything in `medicine.db` file).

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
- **Session**: Represents a conversation with the database.
- **autocommit=False**: Changes aren't saved until you explicitly commit.
- **autoflush=False**: Changes aren't sent to DB automatically.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- **Dependency function**: Used with FastAPI's dependency injection.
- **yield**: Provides the session, then runs cleanup code after.
- **finally**: Always runs, even if there's an error (ensures session is closed).

**Why this matters**: Properly managing database sessions prevents memory leaks and ensures data integrity.

---

### 2. models.py - Database Models (ORM)

**What it does**: Defines the structure of data in the database using SQLAlchemy ORM.

**ORM** = Object-Relational Mapping: Write Python classes instead of SQL.

```python
class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
```

- **Class**: Represents a database table.
- **Columns**: Define table columns (fields).
- **primary_key**: Unique identifier for each record.
- **index**: Makes searches faster on this column.
- **nullable=False**: This field is required.

**Properties** (computed fields):

```python
@property
def days_remaining(self) -> float:
    if self.daily_consumption == 0:
        return 0
    return self.current_amount / self.daily_consumption
```

- **@property**: Access like an attribute but calculated on-the-fly.
- Doesn't store in database, computed each time.
- Example: `drug.days_remaining` (not a method call!)

**Why this matters**: Properties make your code cleaner and prevent data duplication.

---

### 3. schemas.py - Pydantic Models

**What it does**: Validates incoming data and structures outgoing data.

**Pydantic** vs **SQLAlchemy**:
- **SQLAlchemy models**: Database structure (what's stored)
- **Pydantic schemas**: API structure (what's sent/received)

```python
class DrugBase(BaseModel):
    name: str = Field(..., description="Name of the medicine")
    package_size: int = Field(..., gt=0, description="Number of pills per package")
```

- **Field**: Adds validation and documentation.
- **...**: Required field.
- **gt=0**: "Greater than 0" - must be a positive number.

**Inheritance**:

```python
class DrugCreate(DrugBase):
    pass  # Inherits all fields from DrugBase
```

This avoids repeating the same fields.

**Config class**:

```python
class Config:
    from_attributes = True  # Can create from ORM models
```

Allows converting SQLAlchemy model to Pydantic model automatically.

**Why this matters**: Automatic validation prevents bad data from entering your system.

---

### 4. crud.py - Database Operations

**What it does**: All the functions that interact with the database.

**CRUD** = Create, Read, Update, Delete

**Pattern used**:

```python
def get_drug(db: Session, drug_id: int) -> Optional[models.Drug]:
    return db.query(models.Drug).filter(models.Drug.id == drug_id).first()
```

- **db: Session**: Database session parameter.
- **-> Optional[models.Drug]**: Returns Drug or None (type hint).
- **db.query()**: Start a database query.
- **.filter()**: Add conditions (like SQL WHERE).
- **.first()**: Get first result or None.

**Creating records**:

```python
db_drug = models.Drug(**drug.model_dump())
db.add(db_drug)
db.commit()
db.refresh(db_drug)
```

1. **model_dump()**: Convert Pydantic model to dictionary.
2. **add()**: Stage the record for adding.
3. **commit()**: Save changes to database.
4. **refresh()**: Get updated data from database (e.g., auto-generated ID).

**Updating records**:

```python
update_data = drug_update.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(db_drug, field, value)
```

- **exclude_unset=True**: Only fields that were actually provided.
- **setattr()**: Dynamically set object attributes.

**Why this matters**: Separating database logic from API routes makes code maintainable and testable.

---

### 5. email_service.py - Email Functionality

**What it does**: Sends email reminders using SMTP.

**Key concepts**:

```python
async def send_email(self, subject: str, body: str) -> bool:
```

- **async**: Function runs asynchronously (doesn't block).
- **-> bool**: Returns True/False for success.

**SMTP** = Simple Mail Transfer Protocol (how email is sent):

```python
await aiosmtplib.send(
    message,
    hostname=self.smtp_host,
    port=self.smtp_port,
    username=self.smtp_user,
    password=self.smtp_password,
    start_tls=True,
)
```

- **await**: Wait for async operation to complete.
- **start_tls=True**: Encrypt the connection for security.

**String formatting**:

```python
body += f"• {drug.name}\n"
body += f"  Pills remaining: {drug.current_amount}\n"
```

- **f-strings**: Embed variables in strings with `{}`.
- **\n**: Newline character.

**Why this matters**: Async operations allow handling multiple emails without blocking the server.

---

### 6. main.py - FastAPI Application

**What it does**: The heart of the backend - defines all API endpoints and schedules tasks.

**Creating the app**:

```python
app = FastAPI(
    title="Medicine Tracker API",
    description="API for tracking grandma's medicine",
    version="1.0.0",
)
```

This creates the FastAPI application and auto-generates documentation.

**CORS middleware**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- **CORS**: Cross-Origin Resource Sharing - allows frontend to talk to backend.
- **allow_origins=["*"]**: Allow all domains (restrict in production!).

**Route decorators**:

```python
@app.get("/drugs/", response_model=List[schemas.DrugResponse])
async def get_drugs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
```

- **@app.get()**: Handle GET requests to "/drugs/".
- **response_model**: What data shape to return.
- **skip, limit**: Query parameters (e.g., `/drugs/?skip=10&limit=20`).
- **Depends(get_db)**: Dependency injection - FastAPI calls `get_db()` and passes result.

**HTTP status codes**:

```python
@app.post("/drugs/", response_model=schemas.DrugResponse, status_code=201)
```

- **201**: Created (successful POST).
- **200**: OK (default).
- **204**: No Content (successful DELETE).
- **404**: Not Found.

**Error handling**:

```python
if not drug:
    raise HTTPException(status_code=404, detail="Drug not found")
```

Automatically returns JSON error response to client.

**Scheduled tasks**:

```python
scheduler.add_job(
    send_weekly_reminder_job,
    CronTrigger(day_of_week="sun", hour=9, minute=0),
    id="weekly_reminder",
)
```

- **APScheduler**: Runs tasks on a schedule.
- **CronTrigger**: Unix cron-like scheduling.
- Runs in the background while app is running.

**Lifecycle events**:

```python
@app.on_event("startup")
async def startup_event():
    scheduler.start()
```

- Runs when application starts.
- Good for initialization tasks.

**Why this matters**: FastAPI's design makes it easy to build, document, and test APIs.

---

## Frontend Components (Svelte)

### 1. main.js - Entry Point

**What it does**: Initializes the Svelte app.

```javascript
import App from './App.svelte'

const app = new App({
  target: document.getElementById('app')
})
```

- **import**: ES6 module syntax.
- **new App()**: Create instance of the App component.
- **target**: DOM element to mount the app to.

Simple and straightforward!

---

### 2. api.js - API Client

**What it does**: Functions to communicate with the backend.

**Axios setup**:

```javascript
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

- **axios.create()**: Create configured axios instance.
- **baseURL**: Prepended to all requests.

**API functions**:

```javascript
async getAll() {
  const response = await api.get('/drugs/');
  return response.data;
}
```

- **async/await**: Modern way to handle promises.
- **response.data**: Axios wraps data in response object.

**Promise pattern**:

```javascript
drugApi.getAll()
  .then(drugs => console.log(drugs))
  .catch(error => console.error(error))
```

Or with async/await:

```javascript
try {
  const drugs = await drugApi.getAll();
  console.log(drugs);
} catch (error) {
  console.error(error);
}
```

**Why this matters**: Centralizing API calls makes them reusable and easier to update.

---

### 3. App.svelte - Main UI Component

**What it does**: The entire user interface - combines HTML, JavaScript, and CSS.

**Svelte file structure**:

```svelte
<script>
  // JavaScript logic
</script>

<main>
  <!-- HTML template -->
</main>

<style>
  /* CSS styles (scoped to this component) */
</style>
```

**Reactivity**:

```javascript
let drugs = [];
let loading = true;

// Reactive statement - runs when drugs changes
$: drugsNeedingReorder = drugs.filter(d => d.needs_reorder);
```

- **$:**: Reactive declaration.
- Automatically re-runs when dependencies change.

**Lifecycle**:

```javascript
import { onMount } from 'svelte';

onMount(() => {
  loadDrugs();
});
```

- **onMount**: Runs after component is first rendered.
- Perfect for loading initial data.

**Two-way binding**:

```svelte
<input type="text" bind:value={formData.name} />
```

- Input and variable stay in sync automatically.
- Changing input updates variable and vice versa.

**Conditional rendering**:

```svelte
{#if loading}
  <div>Loading...</div>
{:else if drugs.length === 0}
  <div>No drugs</div>
{:else}
  <div>Show drugs</div>
{/if}
```

- **{#if}**: Start conditional block.
- **{:else if}**: Alternative condition.
- **{:else}**: Fallback.
- **{/if}**: End block.

**Loops**:

```svelte
{#each drugs as drug}
  <div>{drug.name}</div>
{/each}
```

- **{#each array as item}**: Loop over array.
- Creates one element per item.

**Event handling**:

```svelte
<button on:click={addDrug}>Add Drug</button>
<button on:click={() => deleteDrug(id)}>Delete</button>
```

- **on:click**: Listen for click events.
- Can pass function or inline arrow function.

**Class binding**:

```svelte
<div class="drug-card" class:needs-reorder={drug.needs_reorder}>
```

- **class:name={condition}**: Add class if condition is true.

**Event modifiers**:

```svelte
<div on:click|stopPropagation>
  <!-- Click won't bubble up -->
</div>

<form on:submit|preventDefault={handleSubmit}>
  <!-- Prevents default form submission -->
</form>
```

**Why this matters**: Svelte's reactivity means you don't manually update the DOM - it happens automatically.

---

## Docker Components

### Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim
```
- **FROM**: Base image to build on.
- Start with Python 3.11 installed.

```dockerfile
WORKDIR /app
```
- Set working directory inside container.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
- **COPY**: Copy files from host to container.
- **RUN**: Execute command during build.
- Install dependencies.

```dockerfile
COPY . .
```
- Copy all application code.

```dockerfile
EXPOSE 8000
```
- Document that this container listens on port 8000.

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
- **CMD**: Command to run when container starts.
- Run uvicorn server.

### Dockerfile (Frontend - Multi-stage)

```dockerfile
FROM node:20-alpine AS builder
```
- **AS builder**: Name this stage.
- **alpine**: Minimal Linux distribution.

```dockerfile
RUN npm run build
```
- Build production version of Svelte app.

```dockerfile
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```
- **FROM**: Start new stage.
- **--from=builder**: Copy from previous stage.
- Only final stage is in the image (smaller size!).

### docker-compose.yml

```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
```

- **services**: Define containers.
- **build**: Build from Dockerfile.
- **ports**: Map host port to container port.

```yaml
    volumes:
      - ./data:/app/data
```

- **volumes**: Persist data outside container.

```yaml
    environment:
      - SMTP_HOST=${SMTP_HOST}
```

- **environment**: Pass environment variables.
- **${VAR}**: Read from .env file.

```yaml
networks:
  medicine-network:
```

- **networks**: Containers can talk to each other by name.

---

## How It All Works Together

### Adding a Drug (Full Flow)

1. **Frontend**: User fills form and clicks "Add Drug"
2. **Svelte**: Calls `drugApi.create(formData)`
3. **Axios**: Sends POST request to `http://localhost:8000/drugs/`
4. **FastAPI**: Route `@app.post("/drugs/")` receives request
5. **Pydantic**: Validates data against `DrugCreate` schema
6. **CRUD**: `create_drug()` adds to database
7. **SQLAlchemy**: Translates to SQL INSERT statement
8. **SQLite**: Stores in `medicine.db` file
9. **FastAPI**: Returns `DrugResponse` (201 Created)
10. **Svelte**: Updates `drugs` array
11. **Svelte Reactivity**: Re-renders UI automatically

### Email Reminder (Scheduled)

1. **Startup**: `scheduler.start()` begins APScheduler
2. **Schedule**: Wait until Sunday 9:00 AM
3. **Trigger**: APScheduler calls `send_weekly_reminder_job()`
4. **Job**: Gets all drugs from database
5. **Email Service**: Formats email body
6. **SMTP**: Connects to Gmail
7. **Send**: Email delivered to recipient
8. **Repeat**: Next Sunday at 9:00 AM

### Deployment (CI/CD)

1. **Developer**: Pushes code to GitHub
2. **GitHub Actions**: Detects push to main branch
3. **Workflow**: Runs jobs defined in `.github/workflows/deploy.yml`
4. **SSH**: Connects to VPS
5. **VPS**: Pulls latest code
6. **Docker**: Rebuilds images
7. **Docker Compose**: Restarts containers
8. **Live**: Updated app is running

---

## Key Takeaways

### FastAPI
- **Fast**: Built on modern async Python
- **Type hints**: Python's type annotations used everywhere
- **Auto docs**: Swagger UI generated automatically
- **Dependency injection**: Clean, testable code
- **Async support**: Handle many requests efficiently

### Svelte
- **Reactive**: UI updates automatically
- **Compiled**: No runtime overhead
- **Simple syntax**: Less boilerplate than React/Vue
- **Scoped styles**: CSS doesn't leak between components
- **Small bundles**: Faster load times

### SQLAlchemy
- **ORM**: Write Python instead of SQL
- **Type safe**: Catch errors before runtime
- **Relationships**: Easy to define table relationships
- **Migrations**: Alembic for schema changes (not used in this simple project)

### Docker
- **Consistency**: Same environment everywhere
- **Isolation**: Dependencies don't conflict
- **Scalability**: Easy to run multiple instances
- **Portability**: Runs on any system with Docker

---

## Learning Path

### To learn more about FastAPI:
1. Read the official tutorial: https://fastapi.tiangolo.com/tutorial/
2. Experiment with adding new endpoints
3. Try adding authentication (FastAPI's security docs)
4. Learn about database migrations with Alembic

### To learn more about Svelte:
1. Official tutorial: https://svelte.dev/tutorial
2. Try creating new components
3. Learn about stores for complex state management
4. Explore SvelteKit for full-stack Svelte apps

### To learn more about Docker:
1. Docker getting started: https://docs.docker.com/get-started/
2. Try creating custom images
3. Learn about volumes and networking
4. Explore Docker best practices

---

## Experimentation Ideas

1. **Add a new field**: Add "prescribing_doctor" to Drug model
2. **New endpoint**: Add endpoint to get drug history/logs
3. **New component**: Create a separate statistics component in Svelte
4. **Styling**: Try different color schemes or layouts
5. **Features**: Add ability to set custom reminder times per drug
6. **Notifications**: Add browser notifications (Web Push API)
7. **Charts**: Add graphs showing medicine consumption over time

Each experiment will teach you more about the technologies!
