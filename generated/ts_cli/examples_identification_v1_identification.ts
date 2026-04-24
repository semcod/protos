import { z } from "zod";

export enum IdentifierType {
  IDENTIFIER_TYPE_UNSPECIFIED = 0,
  IDENTIFIER_TYPE_RFID = 1,
  IDENTIFIER_TYPE_QR = 2,
  IDENTIFIER_TYPE_BARCODE = 3,
  IDENTIFIER_TYPE_MANUAL = 4,
}

export const IdentifyUserCommandSchema = z.object({
  command_id: z.string(),
  identifier: z.string(),
  type: z.nativeEnum(IdentifierType),
});
export type IdentifyUserCommand = z.infer<typeof IdentifyUserCommandSchema>;

export const UserIdentificationReadModelSchema = z.object({
  user_id: z.string(),
  display_name: z.string(),
  roles: z.array(z.string()),
  identified_at: z.string().datetime(),
});
export type UserIdentificationReadModel = z.infer<typeof UserIdentificationReadModelSchema>;

export const UserIdentifiedEventSchema = z.object({
  event_id: z.string(),
  user_id: z.string(),
  type: z.nativeEnum(IdentifierType),
  occurred_at: z.string().datetime(),
});
export type UserIdentifiedEvent = z.infer<typeof UserIdentifiedEventSchema>;
