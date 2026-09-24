import { apiRequest } from "./client";

export type Complaint = {
  id: string;
  status: string;
  description: string;
  location: { latitude: number; longitude: number; label?: string | null };
  images: Array<{ id: string; object_key: string; filename?: string | null; content_type: string; size_bytes: number }>;
  history: Array<{ from_status?: string | null; to_status: string; created_at: string }>;
  created_at: string;
  updated_at: string;
};

export async function submitComplaint(fields: {
  description: string;
  latitude: number;
  longitude: number;
  locationLabel?: string;
  image?: { uri: string; name: string; type: string };
}) {
  const form = new FormData();
  form.append("description", fields.description);
  form.append("latitude", String(fields.latitude));
  form.append("longitude", String(fields.longitude));
  if (fields.locationLabel) form.append("location_label", fields.locationLabel);
  if (fields.image) {
    form.append("image", { uri: fields.image.uri, name: fields.image.name, type: fields.image.type } as unknown as Blob);
  }
  return apiRequest<Complaint>("/complaints", { method: "POST", body: form });
}

export function getComplaints() {
  return apiRequest<Complaint[]>("/complaints");
}

export function getComplaint(id: string) {
  return apiRequest<Complaint>(`/complaints/${encodeURIComponent(id)}`);
}
