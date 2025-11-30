/**
 * API service for communicating with the FastAPI backend.
 *
 * This module provides functions to interact with the medicine tracker API.
 * It uses axios for making HTTP requests and handles the base URL configuration.
 */

import axios from 'axios';

// Base URL for API requests
// In development, requests go through Vite's proxy (/api -> http://localhost:8000)
// In production, set VITE_API_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Drug API functions
 */
export const drugApi = {
  /**
   * Get all drugs from the system.
   *
   * @returns {Promise<Array>} Array of drug objects.
   */
  async getAll() {
    const response = await api.get('/drugs/');
    return response.data;
  },

  /**
   * Get a single drug by ID.
   *
   * @param {number} id - The drug's ID.
   * @returns {Promise<Object>} The drug object.
   */
  async getById(id) {
    const response = await api.get(`/drugs/${id}`);
    return response.data;
  },

  /**
   * Create a new drug.
   *
   * @param {Object} drugData - The drug data to create.
   * @returns {Promise<Object>} The created drug object.
   */
  async create(drugData) {
    const response = await api.post('/drugs/', drugData);
    return response.data;
  },

  /**
   * Update an existing drug.
   *
   * @param {number} id - The drug's ID.
   * @param {Object} updates - Fields to update.
   * @returns {Promise<Object>} The updated drug object.
   */
  async update(id, updates) {
    const response = await api.put(`/drugs/${id}`, updates);
    return response.data;
  },

  /**
   * Delete a drug.
   *
   * @param {number} id - The drug's ID.
   * @returns {Promise<void>}
   */
  async delete(id) {
    await api.delete(`/drugs/${id}`);
  },

  /**
   * Refill a drug (add packages).
   *
   * @param {number} id - The drug's ID.
   * @param {number} packages - Number of packages to add.
   * @returns {Promise<Object>} The updated drug object.
   */
  async refill(id, packages) {
    const response = await api.post(`/drugs/${id}/refill`, { packages });
    return response.data;
  },

  /**
   * Get drugs that need reordering.
   *
   * @returns {Promise<Array>} Array of drugs needing reorder.
   */
  async getNeedingReorder() {
    const response = await api.get('/drugs-status/reorder');
    return response.data;
  },
};

/**
 * Email/reminder API functions
 */
export const reminderApi = {
  /**
   * Send a test email.
   *
   * @returns {Promise<Object>} Response message.
   */
  async sendTestEmail() {
    const response = await api.post('/test-email');
    return response.data;
  },

  /**
   * Manually trigger weekly reminder email.
   *
   * @returns {Promise<Object>} Response message.
   */
  async sendWeeklyReminder() {
    const response = await api.post('/send-weekly-reminder');
    return response.data;
  },

  /**
   * Manually trigger reorder reminder email.
   *
   * @returns {Promise<Object>} Response message.
   */
  async sendReorderReminder() {
    const response = await api.post('/send-reorder-reminder');
    return response.data;
  },
};

/**
 * Doctor Vacation API functions
 */
export const vacationApi = {
  /**
   * Get all doctor vacations.
   *
   * @returns {Promise<Array>} Array of vacation periods.
   */
  async getAll() {
    const response = await api.get('/doctor-vacations/');
    return response.data;
  },

  /**
   * Get current doctor vacation (if doctor is on vacation today).
   *
   * @returns {Promise<Object|null>} Current vacation or null.
   */
  async getCurrent() {
    const response = await api.get('/doctor-vacations/current');
    return response.data;
  },

  /**
   * Create a new doctor vacation period.
   *
   * @param {Object} vacationData - Vacation data (start_date, end_date, notes).
   * @returns {Promise<Object>} The created vacation object.
   */
  async create(vacationData) {
    const response = await api.post('/doctor-vacations/', vacationData);
    return response.data;
  },

  /**
   * Update a doctor vacation period.
   *
   * @param {number} id - The vacation's ID.
   * @param {Object} updates - Fields to update.
   * @returns {Promise<Object>} The updated vacation object.
   */
  async update(id, updates) {
    const response = await api.put(`/doctor-vacations/${id}`, updates);
    return response.data;
  },

  /**
   * Delete a doctor vacation period.
   *
   * @param {number} id - The vacation's ID.
   * @returns {Promise<void>}
   */
  async delete(id) {
    await api.delete(`/doctor-vacations/${id}`);
  },
};
