export interface Release {
  id: number;
  version: string;
  platform: string;
  platform_display: string;
  title: string;
  notes: string;
  notes_lines: string[];
  size_bytes: number | null;
  downloads: number;
  download_url: string;
  created_at: string;
}
