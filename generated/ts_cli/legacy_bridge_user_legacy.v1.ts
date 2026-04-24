import { z } from "zod";

export const LegacyUserSchema = z.object({
  id: z.string(),
  email: z.string(),
  first_name: z.string(),
  last_name: z.string(),
  age: z.number().int(),
  is_active: z.boolean(),
  tags: z.array(z.string()),
});
export type LegacyUser = z.infer<typeof LegacyUserSchema>;
