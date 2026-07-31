export type UserRole = "admin" | "instructor" | "trainee";

export interface AuthSession {
  access_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
}

export interface PhysicalResult {
  id: string;
  raw_value: number;
  computed_grade: "excellent" | "good" | "satisfactory" | "fail" | null;
}

export interface FinalExamination {
  id: string;
  trainee_id: string;
  written_examination: number;
  practical_examination: number;
  pt_test: number;
  bpet: number;
  ppt: number;
  firing_classification: number;
  outdoor_assessment: number;
  indoor_assessment: number;
  field_craft: number;
  battle_craft: number;
  drill_test: number;
  weapon_test: number;
  aggregate_marks: number;
  final_percentage: number;
  merit_position: number | null;
}
