import { z } from "zod";

export const CreateUserCommandSchema = z.object({
  email: z.string(),
  password: z.string(),
});
export type CreateUserCommand = z.infer<typeof CreateUserCommandSchema>;

export const GetUserQuerySchema = z.object({
  id: z.string(),
});
export type GetUserQuery = z.infer<typeof GetUserQuerySchema>;

export const UserSchema = z.object({
  id: z.string(),
  email: z.string(),
});
export type User = z.infer<typeof UserSchema>;
