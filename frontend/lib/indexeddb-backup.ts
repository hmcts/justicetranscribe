import * as Sentry from "@sentry/nextjs";

interface AudioBackup {
  id: string;
  blob: Blob;
  fileName: string;
  timestamp: number;
  mimeType: string;
  recordingDuration?: number;
}

class IndexedDBBackup {
  private dbName = "AudioBackupDB";

  private version = 2;

  private storeName = "audioBackups";

  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = (event) => {
        const errorMsg = (event.target as IDBOpenDBRequest).error?.message || "Unknown error";
        const error = new Error(`Failed to open IndexedDB: ${errorMsg}`);
        console.error("[IndexedDB] Open error:", error);
        Sentry.captureException(error);
        reject(error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log("[IndexedDB] Successfully opened database");
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        console.log("[IndexedDB] Upgrading database to version", this.version);

        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: "id" });
          store.createIndex("timestamp", "timestamp", { unique: false });
          console.log("[IndexedDB] Created object store");
        }
      };
    });
  }

  async saveAudioBackup(backup: AudioBackup): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], "readwrite");
      const store = transaction.objectStore(this.storeName);
      const request = store.put(backup);

      request.onerror = () => {
        reject(new Error("Failed to save audio backup"));
      };

      request.onsuccess = () => {
        resolve();
      };
    });
  }

  async getAudioBackup(id: string): Promise<AudioBackup | null> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], "readonly");
      const store = transaction.objectStore(this.storeName);
      const request = store.get(id);

      request.onerror = () => {
        reject(new Error("Failed to get audio backup"));
      };

      request.onsuccess = () => {
        resolve(request.result || null);
      };
    });
  }

  async getAllAudioBackups(): Promise<AudioBackup[]> {
    if (!this.db) {
      console.log("[IndexedDB] Database not initialized, initializing...");
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], "readonly");
      const store = transaction.objectStore(this.storeName);
      const request = store.getAll();

      request.onerror = (event) => {
        const errorMsg = (event.target as IDBRequest).error?.message || "Unknown error";
        const error = new Error(`Failed to get all audio backups: ${errorMsg}`);
        console.error("[IndexedDB] Get all error:", error);
        Sentry.captureException(error);
        reject(error);
      };

      request.onsuccess = () => {
        const result = request.result || [];
        console.log(`[IndexedDB] Retrieved ${result.length} audio backup(s)`);
        resolve(result);
      };
    });
  }

  async deleteAudioBackup(id: string): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], "readwrite");
      const store = transaction.objectStore(this.storeName);
      const request = store.delete(id);

      request.onerror = () => {
        const error = new Error(`Failed to delete audio backup with id: ${id}`);
        Sentry.captureException(error);
        reject(error);
      };

      request.onsuccess = () => {
        resolve();
      };
    });
  }

  async clearOldBackups(
    maxAge: number = 7 * 24 * 60 * 60 * 1000
  ): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    const cutoffTime = Date.now() - maxAge;
    const backups = await this.getAllAudioBackups();

    // eslint-disable-next-line no-restricted-syntax
    for (const backup of backups) {
      if (backup.timestamp < cutoffTime) {
        // eslint-disable-next-line no-await-in-loop
        await this.deleteAudioBackup(backup.id);
      }
    }
  }

  static generateBackupId(): string {
    return `backup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const audioBackupDB = new IndexedDBBackup();
export { IndexedDBBackup };
export type { AudioBackup };
