<script>
/**
 * Main App Component
 *
 * This is the root component of the medicine tracker application.
 * It manages the entire UI including:
 * - Displaying all drugs in the medicine plan
 * - Adding new drugs
 * - Editing existing drugs
 * - Refilling drugs
 * - Viewing drugs that need reordering
 * - Manually triggering email reminders
 *
 * Svelte Concepts Used:
 * - Reactive statements ($:) - automatically re-run when dependencies change
 * - onMount - lifecycle function that runs when component is first rendered
 * - Stores - (could be added for more complex state management)
 * - Two-way binding with bind:value
 */

import { onMount } from 'svelte';
import { drugApi, reminderApi, vacationApi } from './lib/api';

// State variables
let drugs = [];
let drugsNeedingReorder = [];
let loading = true;
let error = null;
let showAddForm = false;
let showEditForm = false;
let showRefillForm = false;
let selectedDrug = null;

// Doctor vacation state
let vacations = [];
let currentVacation = null;
let showVacationForm = false;
let vacationFormData = {
  start_date: '',
  end_date: '',
  notes: ''
};

// Form data for adding/editing drugs
let formData = {
  name: '',
  dosage_strength: '',
  package_size: 0,
  schedule_type: 'daily',
  morning_pre_food: 0,
  morning_post_food: 0,
  evening_pre_food: 0,
  evening_post_food: 0,
  even_week_pills: 0,
  odd_week_pills: 0,
  current_amount: 0,
  notes: ''
};

/**
 * Load all drugs from the API
 */
async function loadDrugs() {
  try {
    loading = true;
    error = null;
    drugs = await drugApi.getAll();
    drugsNeedingReorder = await drugApi.getNeedingReorder();
  } catch (err) {
    error = 'Fehler beim Laden der Medikamente: ' + err.message;
    console.error(err);
  } finally {
    loading = false;
  }
}

/**
 * Add a new drug
 */
async function addDrug() {
  try {
    await drugApi.create(formData);
    await loadDrugs();
    resetForm();
    showAddForm = false;
  } catch (err) {
    error = 'Fehler beim Hinzufügen: ' + err.message;
  }
}

/**
 * Update an existing drug
 */
async function updateDrug() {
  try {
    await drugApi.update(selectedDrug.id, formData);
    await loadDrugs();
    resetForm();
    showEditForm = false;
  } catch (err) {
    error = 'Fehler beim Aktualisieren: ' + err.message;
  }
}

/**
 * Delete a drug
 */
async function deleteDrug(id) {
  if (!confirm('Möchten Sie dieses Medikament wirklich löschen?')) {
    return;
  }
  try {
    await drugApi.delete(id);
    await loadDrugs();
  } catch (err) {
    error = 'Fehler beim Löschen: ' + err.message;
  }
}

/**
 * Refill a drug
 */
let refillPackages = 1;
async function refillDrug() {
  try {
    await drugApi.refill(selectedDrug.id, refillPackages);
    await loadDrugs();
    showRefillForm = false;
    refillPackages = 1;
  } catch (err) {
    error = 'Fehler beim Auffüllen: ' + err.message;
  }
}

/**
 * Show edit form for a drug
 */
function editDrug(drug) {
  selectedDrug = drug;
  formData = {
    name: drug.name,
    dosage_strength: drug.dosage_strength || '',
    package_size: drug.package_size,
    schedule_type: drug.schedule_type || 'daily',
    morning_pre_food: drug.morning_pre_food,
    morning_post_food: drug.morning_post_food,
    evening_pre_food: drug.evening_pre_food,
    evening_post_food: drug.evening_post_food,
    even_week_pills: drug.even_week_pills || 0,
    odd_week_pills: drug.odd_week_pills || 0,
    current_amount: drug.current_amount,
    notes: drug.notes || ''
  };
  showEditForm = true;
}

/**
 * Show refill form for a drug
 */
function openRefillForm(drug) {
  selectedDrug = drug;
  showRefillForm = true;
}

/**
 * Reset form data
 */
function resetForm() {
  formData = {
    name: '',
    dosage_strength: '',
    package_size: 0,
    schedule_type: 'daily',
    morning_pre_food: 0,
    morning_post_food: 0,
    evening_pre_food: 0,
    evening_post_food: 0,
    even_week_pills: 0,
    odd_week_pills: 0,
    current_amount: 0,
    notes: ''
  };
  selectedDrug = null;
}

/**
 * Send test email
 */
async function sendTestEmail() {
  try {
    const result = await reminderApi.sendTestEmail();
    alert(result.message);
  } catch (err) {
    alert('Fehler beim Senden der Test-E-Mail: ' + err.message);
  }
}

/**
 * Send weekly reminder
 */
async function sendWeeklyReminder() {
  try {
    const result = await reminderApi.sendWeeklyReminder();
    alert(result.message);
  } catch (err) {
    alert('Fehler beim Senden der Erinnerung: ' + err.message);
  }
}

/**
 * Send reorder reminder
 */
async function sendReorderReminder() {
  try {
    const result = await reminderApi.sendReorderReminder();
    alert(result.message);
  } catch (err) {
    alert('Fehler beim Senden der Erinnerung: ' + err.message);
  }
}

/**
 * Subtract a week's worth of pills from all drugs
 */
async function subtractWeeklyUsage() {
  if (!confirm('Medikamente für die Woche gestellt?\n\nDies zieht eine Woche an Tabletten von allen Medikamenten ab.')) {
    return;
  }

  try {
    let updatedCount = 0;

    for (const drug of drugs) {
      // Calculate weekly consumption
      let weeklyConsumption;
      if (drug.schedule_type === 'weekly_alternating') {
        weeklyConsumption = drug.current_week_pills;
      } else {
        // Daily schedule: calculate daily consumption * 7
        const dailyConsumption = drug.morning_pre_food + drug.morning_post_food +
                                 drug.evening_pre_food + drug.evening_post_food;
        weeklyConsumption = dailyConsumption * 7;
      }

      // Calculate new amount
      const newAmount = Math.max(0, drug.current_amount - weeklyConsumption);

      // Update the drug
      await drugApi.update(drug.id, { current_amount: newAmount });
      updatedCount++;
    }

    await loadDrugs();
    alert(`${updatedCount} Medikament(e) erfolgreich aktualisiert.\nWochenverbrauch wurde abgezogen.`);
  } catch (err) {
    error = 'Fehler beim Abziehen des Wochenverbrauchs: ' + err.message;
  }
}

/**
 * Load doctor vacations
 */
async function loadVacations() {
  try {
    vacations = await vacationApi.getAll();
    currentVacation = await vacationApi.getCurrent();
  } catch (err) {
    console.error('Failed to load vacations:', err);
  }
}

/**
 * Add a new doctor vacation
 */
async function addVacation() {
  try {
    await vacationApi.create(vacationFormData);
    await loadVacations();
    vacationFormData = { start_date: '', end_date: '', notes: '' };
    showVacationForm = false;
  } catch (err) {
    error = 'Fehler beim Hinzufügen des Urlaubs: ' + err.message;
  }
}

/**
 * Delete a doctor vacation
 */
async function deleteVacation(id) {
  if (confirm('Diesen Urlaubszeitraum löschen?')) {
    try {
      await vacationApi.delete(id);
      await loadVacations();
    } catch (err) {
      error = 'Fehler beim Löschen des Urlaubs: ' + err.message;
    }
  }
}

// Reactive statement to find next upcoming vacation
$: nextVacation = vacations
  .filter(v => v.is_upcoming)
  .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))[0] || null;

// Load drugs and vacations when component mounts
onMount(() => {
  loadDrugs();
  loadVacations();
});
</script>

<main>
  <header>
    <h1>💊 Medikamenten-Tracker</h1>
    <p>Medikamente verwalten und Nachbestellungen im Blick behalten</p>
  </header>

  {#if error}
    <div class="error-banner">
      {error}
      <button on:click={() => error = null}>✕</button>
    </div>
  {/if}

  <div class="container">
    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="primary-actions">
        <button class="btn btn-primary" on:click={() => showAddForm = true}>
          + Neues Medikament
        </button>
        <button class="btn btn-success" on:click={subtractWeeklyUsage}>
          ✓ Woche gestellt
        </button>
      </div>
      <div class="reminder-actions">
        <button class="btn btn-secondary" on:click={sendWeeklyReminder}>
          Wochenerinnerung senden
        </button>
        <button class="btn btn-secondary" on:click={sendReorderReminder}>
          Bestellerinnerung senden
        </button>
        <button class="btn btn-outline" on:click={sendTestEmail}>
          Test-E-Mail
        </button>
      </div>
    </div>

    <!-- Doctor Availability - Compact -->
    <div class="doctor-status-card">
      <div class="doctor-status-info">
        {#if currentVacation}
          <span class="status-indicator unavailable">⚠️</span>
          <div class="status-text">
            <strong>Arzt im Urlaub</strong>
            <span class="status-detail">Bis {new Date(currentVacation.end_date).toLocaleDateString('de-DE')}</span>
          </div>
        {:else}
          <span class="status-indicator available">✓</span>
          <div class="status-text">
            <strong>Arzt verfügbar</strong>
            {#if nextVacation}
              <span class="status-detail">Nächster Urlaub: {new Date(nextVacation.start_date).toLocaleDateString('de-DE')}</span>
            {/if}
          </div>
        {/if}
      </div>
      <button class="btn btn-sm btn-outline" on:click={() => showVacationForm = !showVacationForm}>
        {showVacationForm ? 'Schließen' : 'Verwalten'}
      </button>
    </div>

    <!-- Vacation Management Form (collapsible) -->
    {#if showVacationForm}
      <div class="vacation-manager">
        <h3>Arzt-Urlaube verwalten</h3>

        <!-- Add Form -->
        <form on:submit|preventDefault={addVacation} class="vacation-add-form">
          <div class="form-row-compact">
            <input type="date" bind:value={vacationFormData.start_date} placeholder="Start" required />
            <input type="date" bind:value={vacationFormData.end_date} placeholder="Ende" required />
            <input type="text" bind:value={vacationFormData.notes} placeholder="Notizen (optional)" />
            <button type="submit" class="btn btn-sm btn-success">Hinzufügen</button>
          </div>
        </form>

        <!-- Vacation List -->
        {#if vacations.length > 0}
          <div class="vacation-list-compact">
            {#each vacations as vacation}
              <div class="vacation-row" class:past={vacation.is_past}>
                <div class="vacation-info-compact">
                  <span class="vacation-dates-compact">
                    {new Date(vacation.start_date).toLocaleDateString('de-DE')} - {new Date(vacation.end_date).toLocaleDateString('de-DE')}
                  </span>
                  {#if vacation.notes}
                    <span class="vacation-note-compact">{vacation.notes}</span>
                  {/if}
                  <span class="badge-compact" class:badge-current={vacation.is_current} class:badge-upcoming={vacation.is_upcoming} class:badge-past={vacation.is_past}>
                    {vacation.is_current ? 'Aktuell' : vacation.is_upcoming ? 'Bevorstehend' : 'Vergangen'}
                  </span>
                </div>
                <button class="btn btn-danger btn-xs" on:click={() => deleteVacation(vacation.id)}>×</button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Reorder Alert -->
    {#if drugsNeedingReorder.length > 0}
      <div class="alert alert-warning">
        <strong>⚠️ {drugsNeedingReorder.length} Medikament(e) müssen nachbestellt werden!</strong>
        <p>Weniger als 3 Wochen Vorrat</p>
      </div>
    {/if}

    <!-- Drugs List -->
    {#if loading}
      <div class="loading">Lädt...</div>
    {:else if drugs.length === 0}
      <div class="empty-state">
        <p>Noch keine Medikamente im System.</p>
        <p>Klicken Sie auf "Neues Medikament", um zu beginnen.</p>
      </div>
    {:else}
      <div class="drugs-grid">
        {#each drugs as drug}
          <div class="drug-card" class:needs-reorder={drug.needs_reorder}>
            <div class="drug-header">
              <h3>
                {drug.name}
                {#if drug.dosage_strength}
                  <span class="dosage-strength">{drug.dosage_strength}</span>
                {/if}
              </h3>
              {#if drug.schedule_type === 'weekly_alternating'}
                <span class="badge badge-alternating">Woche {drug.current_week_type === 'even' ? 'Gerade' : 'Ungerade'}</span>
              {/if}
              {#if drug.needs_reorder}
                <span class="badge badge-warning">Niedriger Bestand</span>
              {/if}
            </div>

            <div class="drug-info">
              {#if drug.schedule_type === 'weekly_alternating'}
                <!-- Weekly Alternating Schedule -->
                <div class="dosage-section alternating-schedule">
                  <div class="dosage-label">Wöchentlich wechselnder Plan:</div>
                  <div class="week-schedule">
                    <div class="week-item" class:active={drug.current_week_type === 'even'}>
                      <strong>Gerade Wochen:</strong> {drug.even_week_pills} Tabl./Woche
                    </div>
                    <div class="week-item" class:active={drug.current_week_type === 'odd'}>
                      <strong>Ungerade Wochen:</strong> {drug.odd_week_pills} Tabl./Woche
                    </div>
                  </div>
                  <div class="current-week-info">
                    Diese Woche: <strong>{drug.current_week_pills} Tabletten</strong>
                  </div>
                </div>
              {:else}
                <!-- Daily Schedule -->
                <div class="dosage-section">
                  <div class="dosage-label">Morgens:</div>
                  <div class="dosage-details">
                    {#if drug.morning_pre_food > 0}
                      <span class="dose">Vor dem Essen: {drug.morning_pre_food}</span>
                    {/if}
                    {#if drug.morning_post_food > 0}
                      <span class="dose">Nach dem Essen: {drug.morning_post_food}</span>
                    {/if}
                    {#if drug.morning_pre_food === 0 && drug.morning_post_food === 0}
                      <span class="dose-none">Keine</span>
                    {/if}
                  </div>
                </div>

                <div class="dosage-section">
                  <div class="dosage-label">Abends:</div>
                  <div class="dosage-details">
                    {#if drug.evening_pre_food > 0}
                      <span class="dose">Vor dem Essen: {drug.evening_pre_food}</span>
                    {/if}
                    {#if drug.evening_post_food > 0}
                      <span class="dose">Nach dem Essen: {drug.evening_post_food}</span>
                    {/if}
                    {#if drug.evening_pre_food === 0 && drug.evening_post_food === 0}
                      <span class="dose-none">Keine</span>
                    {/if}
                  </div>
                </div>
              {/if}

              {#if drug.notes}
                <div class="info-row">
                  <span class="label">Notizen:</span>
                  <span class="notes">{drug.notes}</span>
                </div>
              {/if}

              <div class="info-row">
                <span class="label">Tagesbedarf:</span>
                <span>{drug.daily_consumption.toFixed(2)} Tabl./Tag (Ø)</span>
              </div>
              <div class="info-row">
                <span class="label">Packungsgröße:</span>
                <span>{drug.package_size} Tabletten</span>
              </div>
              <div class="info-row">
                <span class="label">Aktueller Bestand:</span>
                <span class="highlight">{drug.current_amount} Tabletten</span>
              </div>
              <div class="info-row">
                <span class="label">Verbleibende Zeit:</span>
                <span class:low-stock={drug.needs_reorder}>
                  {drug.weeks_remaining.toFixed(1)} Wochen ({drug.days_remaining.toFixed(0)} Tage)
                </span>
              </div>
            </div>

            <div class="drug-actions">
              <button class="btn btn-sm btn-success" on:click={() => openRefillForm(drug)}>
                Auffüllen
              </button>
              <button class="btn btn-sm btn-secondary" on:click={() => editDrug(drug)}>
                Bearbeiten
              </button>
              <button class="btn btn-sm btn-danger" on:click={() => deleteDrug(drug.id)}>
                Löschen
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Add Drug Modal -->
  {#if showAddForm}
    <div class="modal-backdrop" on:click={() => showAddForm = false}>
      <div class="modal" on:click|stopPropagation>
        <h2>Neues Medikament hinzufügen</h2>
        <form on:submit|preventDefault={addDrug}>
          <div class="form-group">
            <label>Medikamentenname *</label>
            <input type="text" bind:value={formData.name} required />
          </div>
          <div class="form-group">
            <label>Dosisstärke (optional)</label>
            <input type="text" bind:value={formData.dosage_strength} placeholder="z.B. 75µg, 100mg" />
            <small>µ für Mikrogramm (Alt+0181 auf Windows)</small>
          </div>
          <div class="form-group">
            <label>Packungsgröße (Tabletten pro Packung) *</label>
            <input type="number" bind:value={formData.package_size} min="1" required />
          </div>

          <div class="form-group">
            <label>Einnahmeplan *</label>
            <select bind:value={formData.schedule_type}>
              <option value="daily">Täglich</option>
              <option value="weekly_alternating">Wöchentlich wechselnd</option>
            </select>
            <small>Wählen Sie "Wöchentlich wechselnd" für unterschiedliche Dosierungen in geraden/ungeraden Wochen</small>
          </div>

          {#if formData.schedule_type === 'daily'}
            <div class="dosage-form-section">
              <h3>Morgendosis</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Vor dem Essen</label>
                  <input type="number" bind:value={formData.morning_pre_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
                <div class="form-group">
                  <label>Nach dem Essen</label>
                  <input type="number" bind:value={formData.morning_post_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
              </div>
            </div>

            <div class="dosage-form-section">
              <h3>Abenddosis</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Vor dem Essen</label>
                  <input type="number" bind:value={formData.evening_pre_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
                <div class="form-group">
                  <label>Nach dem Essen</label>
                  <input type="number" bind:value={formData.evening_post_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
              </div>
            </div>
          {:else}
            <div class="dosage-form-section">
              <h3>Wöchentlich wechselnder Plan</h3>
              <p class="help-text">Geben Sie die Gesamtanzahl der Tabletten pro Woche für gerade und ungerade Wochen ein</p>
              <div class="form-row">
                <div class="form-group">
                  <label>Gerade Wochen (Tabl./Woche)</label>
                  <input type="number" bind:value={formData.even_week_pills} min="0" step="0.5" />
                  <small>Gesamt-Tabletten in geraden Wochen</small>
                </div>
                <div class="form-group">
                  <label>Ungerade Wochen (Tabl./Woche)</label>
                  <input type="number" bind:value={formData.odd_week_pills} min="0" step="0.5" />
                  <small>Gesamt-Tabletten in ungeraden Wochen</small>
                </div>
              </div>
              <p class="help-text">Hinweis: Für tägliche Einnahmezeiten (z.B. 1 Tablette morgens vor dem Essen) können Sie diese unten einstellen</p>
              <div class="form-row">
                <div class="form-group">
                  <label>Morgens (vor dem Essen)</label>
                  <input type="number" bind:value={formData.morning_pre_food} min="0" step="0.5" />
                </div>
                <div class="form-group">
                  <label>Morgens (nach dem Essen)</label>
                  <input type="number" bind:value={formData.morning_post_food} min="0" step="0.5" />
                </div>
              </div>
            </div>
          {/if}

          <div class="form-group">
            <label>Aktueller Bestand (Tabletten)</label>
            <input type="number" bind:value={formData.current_amount} min="0" step="0.5" />
          </div>
          <div class="form-group">
            <label>Notizen (optional)</label>
            <textarea bind:value={formData.notes} rows="2" placeholder="Besondere Hinweise..."></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" on:click={() => { showAddForm = false; resetForm(); }}>
              Abbrechen
            </button>
            <button type="submit" class="btn btn-primary">Hinzufügen</button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  <!-- Edit Drug Modal -->
  {#if showEditForm}
    <div class="modal-backdrop" on:click={() => showEditForm = false}>
      <div class="modal" on:click|stopPropagation>
        <h2>Medikament bearbeiten</h2>
        <form on:submit|preventDefault={updateDrug}>
          <div class="form-group">
            <label>Medikamentenname *</label>
            <input type="text" bind:value={formData.name} required />
          </div>
          <div class="form-group">
            <label>Dosisstärke (optional)</label>
            <input type="text" bind:value={formData.dosage_strength} placeholder="z.B. 75µg, 100mg" />
            <small>µ für Mikrogramm (Alt+0181 auf Windows)</small>
          </div>
          <div class="form-group">
            <label>Packungsgröße (Tabletten pro Packung) *</label>
            <input type="number" bind:value={formData.package_size} min="1" required />
          </div>

          <div class="form-group">
            <label>Einnahmeplan *</label>
            <select bind:value={formData.schedule_type}>
              <option value="daily">Täglich</option>
              <option value="weekly_alternating">Wöchentlich wechselnd</option>
            </select>
            <small>Wählen Sie "Wöchentlich wechselnd" für unterschiedliche Dosierungen in geraden/ungeraden Wochen</small>
          </div>

          {#if formData.schedule_type === 'daily'}
            <div class="dosage-form-section">
              <h3>Morgendosis</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Vor dem Essen</label>
                  <input type="number" bind:value={formData.morning_pre_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
                <div class="form-group">
                  <label>Nach dem Essen</label>
                  <input type="number" bind:value={formData.morning_post_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
              </div>
            </div>

            <div class="dosage-form-section">
              <h3>Abenddosis</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>Vor dem Essen</label>
                  <input type="number" bind:value={formData.evening_pre_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
                <div class="form-group">
                  <label>Nach dem Essen</label>
                  <input type="number" bind:value={formData.evening_post_food} min="0" step="0.5" />
                  <small>0.5 für halbe Tabletten möglich</small>
                </div>
              </div>
            </div>
          {:else}
            <div class="dosage-form-section">
              <h3>Wöchentlich wechselnder Plan</h3>
              <p class="help-text">Geben Sie die Gesamtanzahl der Tabletten pro Woche für gerade und ungerade Wochen ein</p>
              <div class="form-row">
                <div class="form-group">
                  <label>Gerade Wochen (Tabl./Woche)</label>
                  <input type="number" bind:value={formData.even_week_pills} min="0" step="0.5" />
                  <small>Gesamt-Tabletten in geraden Wochen</small>
                </div>
                <div class="form-group">
                  <label>Ungerade Wochen (Tabl./Woche)</label>
                  <input type="number" bind:value={formData.odd_week_pills} min="0" step="0.5" />
                  <small>Gesamt-Tabletten in ungeraden Wochen</small>
                </div>
              </div>
              <p class="help-text">Hinweis: Für tägliche Einnahmezeiten (z.B. 1 Tablette morgens vor dem Essen) können Sie diese unten einstellen</p>
              <div class="form-row">
                <div class="form-group">
                  <label>Morgens (vor dem Essen)</label>
                  <input type="number" bind:value={formData.morning_pre_food} min="0" step="0.5" />
                </div>
                <div class="form-group">
                  <label>Morgens (nach dem Essen)</label>
                  <input type="number" bind:value={formData.morning_post_food} min="0" step="0.5" />
                </div>
              </div>
            </div>
          {/if}

          <div class="form-group">
            <label>Aktueller Bestand (Tabletten)</label>
            <input type="number" bind:value={formData.current_amount} min="0" step="0.5" />
          </div>
          <div class="form-group">
            <label>Notizen (optional)</label>
            <textarea bind:value={formData.notes} rows="2" placeholder="Besondere Hinweise..."></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" on:click={() => { showEditForm = false; resetForm(); }}>
              Abbrechen
            </button>
            <button type="submit" class="btn btn-primary">Aktualisieren</button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  <!-- Refill Modal -->
  {#if showRefillForm && selectedDrug}
    <div class="modal-backdrop" on:click={() => showRefillForm = false}>
      <div class="modal" on:click|stopPropagation>
        <h2>{selectedDrug.name} auffüllen</h2>
        <p class="modal-info">Packungsgröße: {selectedDrug.package_size} Tabletten</p>
        <form on:submit|preventDefault={refillDrug}>
          <div class="form-group">
            <label>Anzahl Packungen</label>
            <input type="number" bind:value={refillPackages} min="1" required />
            <small>Dies fügt {refillPackages * selectedDrug.package_size} Tabletten hinzu</small>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" on:click={() => showRefillForm = false}>
              Abbrechen
            </button>
            <button type="submit" class="btn btn-success">Auffüllen</button>
          </div>
        </form>
      </div>
    </div>
  {/if}

</main>

<style>
  /* Global Styles */
  :global(body) {
    margin: 0;
    padding: 0;
  }

  main {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 1rem;
  }

  header {
    text-align: center;
    color: white;
    margin-bottom: 2rem;
  }

  h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  header p {
    opacity: 0.9;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
  }

  /* Error Banner */
  .error-banner {
    background: #ff4444;
    color: white;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .error-banner button {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
  }

  /* Actions Bar */
  .actions-bar {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .primary-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .reminder-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  /* Alert */
  .alert {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
  }

  .alert-warning {
    background: #fff3cd;
    border: 2px solid #ffc107;
    color: #856404;
  }

  .alert strong {
    display: block;
    margin-bottom: 0.25rem;
  }

  /* Loading & Empty States */
  .loading, .empty-state {
    background: white;
    padding: 3rem;
    border-radius: 12px;
    text-align: center;
    color: #666;
  }

  /* Drugs Grid */
  .drugs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .drug-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .drug-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
  }

  .drug-card.needs-reorder {
    border: 2px solid #ff9800;
  }

  .drug-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .drug-header h3 {
    margin: 0;
    color: #333;
    flex: 1;
  }

  .badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .badge-alternating {
    background: #e8eaf6;
    color: #5e35b1;
  }

  .badge-quarterly {
    background: #e3f2fd;
    color: #1976d2;
  }

  .badge-warning {
    background: #fff3cd;
    color: #856404;
  }

  .drug-info {
    margin-bottom: 1rem;
  }

  .dosage-section {
    background: #f8f9fa;
    padding: 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.75rem;
  }

  .alternating-schedule {
    background: #e8eaf6;
  }

  .week-schedule {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .week-item {
    flex: 1;
    padding: 0.5rem;
    background: white;
    border-radius: 4px;
    font-size: 0.85rem;
    opacity: 0.6;
  }

  .week-item.active {
    opacity: 1;
    border: 2px solid #5e35b1;
    font-weight: 600;
  }

  .current-week-info {
    text-align: center;
    padding: 0.5rem;
    background: white;
    border-radius: 4px;
    font-size: 0.9rem;
    color: #5e35b1;
  }

  .dosage-label {
    font-weight: 600;
    color: #555;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .dosage-details {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .dose {
    background: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #333;
  }

  .dose-none {
    color: #999;
    font-style: italic;
    font-size: 0.85rem;
  }

  .notes {
    font-style: italic;
    color: #666;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #f0f0f0;
  }

  .info-row:last-child {
    border-bottom: none;
  }

  .label {
    color: #666;
    font-weight: 500;
  }

  .highlight {
    font-weight: 600;
    color: #667eea;
  }

  .low-stock {
    color: #ff9800;
    font-weight: 600;
  }

  .drug-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  /* Buttons */
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .btn-primary {
    background: #667eea;
    color: white;
  }

  .btn-primary:hover {
    background: #5568d3;
  }

  .btn-secondary {
    background: #6c757d;
    color: white;
  }

  .btn-secondary:hover {
    background: #5a6268;
  }

  .btn-success {
    background: #28a745;
    color: white;
  }

  .btn-success:hover {
    background: #218838;
  }

  .btn-danger {
    background: #dc3545;
    color: white;
  }

  .btn-danger:hover {
    background: #c82333;
  }

  .btn-outline {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
  }

  .btn-outline:hover {
    background: #667eea;
    color: white;
  }

  /* Modal */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal h2 {
    margin-top: 0;
    color: #333;
  }

  .modal-info {
    color: #666;
    margin-bottom: 1rem;
  }

  /* Forms */
  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    color: #333;
    font-weight: 500;
  }

  input[type="text"],
  input[type="number"],
  select,
  textarea {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;
    font-family: inherit;
  }

  select {
    cursor: pointer;
    background: white;
  }

  textarea {
    resize: vertical;
    min-height: 60px;
  }

  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: #667eea;
  }

  .help-text {
    margin: 0.5rem 0;
    color: #666;
    font-size: 0.875rem;
    font-style: italic;
  }

  .dosage-form-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
  }

  .dosage-form-section h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: #555;
  }

  small {
    display: block;
    margin-top: 0.25rem;
    color: #666;
    font-size: 0.875rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .checkbox-label input[type="checkbox"] {
    width: auto;
    cursor: pointer;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 2rem;
  }

  /* Doctor Availability - Compact Styles */
  .doctor-status-card {
    background: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .doctor-status-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .status-indicator {
    font-size: 1.5rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }

  .status-indicator.available {
    background: #e8f5e9;
    color: #4caf50;
  }

  .status-indicator.unavailable {
    background: #fff3cd;
    color: #ff9800;
  }

  .status-text {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .status-text strong {
    font-size: 1rem;
    color: #333;
  }

  .status-detail {
    font-size: 0.875rem;
    color: #666;
  }

  .vacation-manager {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .vacation-manager h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: #333;
  }

  .vacation-add-form {
    margin-bottom: 1.5rem;
  }

  .form-row-compact {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .form-row-compact input {
    flex: 1;
    min-width: 140px;
  }

  .form-row-compact input[type="text"] {
    flex: 2;
  }

  .vacation-list-compact {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .vacation-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
  }

  .vacation-row.past {
    opacity: 0.5;
  }

  .vacation-info-compact {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    flex: 1;
  }

  .vacation-dates-compact {
    font-weight: 600;
    font-size: 0.875rem;
    color: #333;
  }

  .vacation-note-compact {
    font-size: 0.875rem;
    color: #666;
    font-style: italic;
  }

  .badge-compact {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .badge-current {
    background: #fff3cd;
    color: #856404;
  }

  .badge-upcoming {
    background: #e3f2fd;
    color: #1976d2;
  }

  .badge-past {
    background: #f5f5f5;
    color: #999;
  }

  .btn-xs {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
    min-width: auto;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .drugs-grid {
      grid-template-columns: 1fr;
    }

    .actions-bar {
      flex-direction: column;
      align-items: stretch;
    }

    .primary-actions {
      flex-direction: column;
    }

    .reminder-actions {
      flex-direction: column;
    }

    .form-row {
      grid-template-columns: 1fr;
    }

    .form-row-compact {
      flex-direction: column;
      align-items: stretch;
    }

    .form-row-compact input {
      width: 100%;
    }

    .doctor-status-card {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .vacation-info-compact {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    h1 {
      font-size: 2rem;
    }
  }
</style>
