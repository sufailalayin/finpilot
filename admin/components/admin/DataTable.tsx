"use client";

import React from "react";

export interface Column<T> {
  key: string;
  header: string;
  width?: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  align?: "left" | "center" | "right";
}

interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  pagination?: PaginationConfig;
  sortKey?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (key: string) => void;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading = false,
  emptyMessage = "No records found",
  pagination,
  sortKey,
  sortOrder = "desc",
  onSort,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="datatable-root">
      <div className="datatable-scroll">
        <table className="datatable-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                return (
                  <th
                    key={col.key}
                    style={{ width: col.width, textAlign: col.align || "left" }}
                    className={col.sortable ? "sortable-header" : ""}
                    onClick={() => col.sortable && onSort?.(col.key)}
                  >
                    <div className="th-content">
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className={`sort-arrow ${isSorted ? "active" : ""}`}>
                          {isSorted ? (sortOrder === "asc" ? "▲" : "▼") : "⇅"}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, rIdx) => (
                <tr key={rIdx} className="loading-row">
                  {columns.map((col, cIdx) => (
                    <td key={cIdx}>
                      <div className="table-skeleton" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="datatable-empty">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr
                  key={keyExtractor(row)}
                  onClick={() => onRowClick?.(row)}
                  className={onRowClick ? "clickable-row" : ""}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      style={{ textAlign: col.align || "left" }}
                    >
                      {col.render
                        ? col.render(row, idx)
                        : (row as Record<string, unknown>)[col.key] !== undefined
                          ? String((row as Record<string, unknown>)[col.key] ?? "")
                          : "—"}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination && (
        <div className="datatable-pagination">
          <div className="pagination-info">
            Showing{" "}
            <strong>
              {pagination.total > 0
                ? (pagination.page - 1) * pagination.pageSize + 1
                : 0}
            </strong>{" "}
            to{" "}
            <strong>
              {Math.min(pagination.page * pagination.pageSize, pagination.total)}
            </strong>{" "}
            of <strong>{pagination.total.toLocaleString()}</strong> records
          </div>

          <div className="pagination-controls">
            {pagination.onPageSizeChange && (
              <select
                className="page-size-select"
                value={pagination.pageSize}
                onChange={(e) =>
                  pagination.onPageSizeChange?.(Number(e.target.value))
                }
              >
                <option value={10}>10 / page</option>
                <option value={25}>25 / page</option>
                <option value={50}>50 / page</option>
                <option value={100}>100 / page</option>
              </select>
            )}

            <button
              className="pagination-btn"
              disabled={pagination.page <= 1 || loading}
              onClick={() => pagination.onPageChange(pagination.page - 1)}
            >
              Previous
            </button>

            <span className="pagination-current">
              Page {pagination.page} of {Math.max(pagination.totalPages, 1)}
            </span>

            <button
              className="pagination-btn"
              disabled={
                pagination.page >= pagination.totalPages || loading
              }
              onClick={() => pagination.onPageChange(pagination.page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
