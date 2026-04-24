import { z } from "zod";

export const IndexEntryCommandSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string(),
  content: z.string(),
  metadata: z.record(z.string(), z.string()),
});
export type IndexEntryCommand = z.infer<typeof IndexEntryCommandSchema>;

export const EntryIndexedSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string(),
  timestamp: z.number(),
});
export type EntryIndexed = z.infer<typeof EntryIndexedSchema>;

export const SearchRequestSchema = z.object({
  query: z.string(),
  category_filter: z.string(),
  limit: z.number().int(),
});
export type SearchRequest = z.infer<typeof SearchRequestSchema>;

export const SearchResponseSchema = z.object({
  results: z.array(z.lazy(() => ResultSchema)),
  total_count: z.number().int(),
});
export type SearchResponse = z.infer<typeof SearchResponseSchema>;

export const ResultSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string(),
  score: z.number(),
});
export type Result = z.infer<typeof ResultSchema>;
