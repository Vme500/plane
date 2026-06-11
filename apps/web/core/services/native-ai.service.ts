/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { APIService } from "@/services/api.service";

export class NativeAIService extends APIService {
  constructor() {
    super("");
  }

  async getStatus(workspaceSlug: string): Promise<Record<string, unknown>> {
    return this.get(`/api/workspaces/${workspaceSlug}/ai-assistant/native/status/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response;
      });
  }

  async propose(
    workspaceSlug: string,
    data: { message: string; context?: { project_id?: string; project_name?: string } }
  ): Promise<Record<string, unknown>> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-assistant/native/propose/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response;
      });
  }
}
