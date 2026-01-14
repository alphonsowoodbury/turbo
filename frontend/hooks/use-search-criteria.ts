"use client";

import { useState, useEffect } from "react";

export interface SearchCriteria {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  job_titles?: string[];
  locations?: string[];
  excluded_states?: string[];
  remote_policies?: string[];
  exclude_onsite: boolean;
  salary_minimum?: number;
  salary_target?: number;
  required_keywords?: string[];
  preferred_keywords?: string[];
  excluded_keywords?: string[];
  company_sizes?: string[];
  industries?: string[];
  excluded_industries?: string[];
  enabled_sources?: string[];
  auto_search_enabled: boolean;
  search_frequency_hours: number;
  last_search_at?: string;
  next_search_at?: string;
  scoring_weights?: {
    salary?: number;
    location?: number;
    keywords?: number;
    title?: number;
  };
  created_at: string;
  updated_at: string;
}

export interface SearchHistory {
  id: string;
  search_criteria_id: string;
  source: string;
  query_params?: Record<string, any>;
  jobs_found: number;
  jobs_matched: number;
  jobs_new: number;
  status: string;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  created_at: string;
}

interface UseSearchCriteriaOptions {
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export function useSearchCriteria(options: UseSearchCriteriaOptions = {}) {
  const [criteria, setCriteria] = useState<SearchCriteria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCriteria = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (options.is_active !== undefined) {
        params.append("is_active", options.is_active.toString());
      }
      if (options.limit) params.append("limit", options.limit.toString());
      if (options.offset) params.append("offset", options.offset.toString());

      const response = await fetch(`/api/v1/job-search/criteria?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch search criteria: ${response.statusText}`);
      }

      const data = await response.json();
      setCriteria(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Error fetching search criteria:", err);
    } finally {
      setLoading(false);
    }
  };

  const executeSearch = async (criteriaId: string) => {
    try {
      const response = await fetch(`/api/v1/job-search/execute/${criteriaId}`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Failed to execute search: ${response.statusText}`);
      }

      const result = await response.json();

      // Refetch criteria to get updated last_search_at
      await fetchCriteria();

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to execute search");
      console.error("Error executing search:", err);
      throw err;
    }
  };

  useEffect(() => {
    fetchCriteria();
  }, [options.is_active, options.limit, options.offset]);

  return {
    criteria,
    loading,
    error,
    refetch: fetchCriteria,
    executeSearch,
  };
}

export function useSearchHistory(criteriaId?: string) {
  const [history, setHistory] = useState<SearchHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (criteriaId) params.append("criteria_id", criteriaId);

      const response = await fetch(`/api/v1/job-search/history?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch search history: ${response.statusText}`);
      }

      const data = await response.json();
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Error fetching search history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [criteriaId]);

  return {
    history,
    loading,
    error,
    refetch: fetchHistory,
  };
}
