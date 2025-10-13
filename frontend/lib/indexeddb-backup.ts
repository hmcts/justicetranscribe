import * as Sentry from "@sentry/nextjs";

interface AudioBackup {
  id: string;
  blob: Blob;
  fileName: string;
  timestamp: number;
  mimeType: string;
  recordingDuration?: number;
}

interface AudioChunk {
  id: string;
  chunkIndex: number;
  data: Blob;
  timestamp: number;
}

class IndexedDBBackup {
  private dbName = "AudioBackupDB";

<<<<<<< HEAD
  private version = 2; // Incremented to add chunks store
=======
  private version = 2;
>>>>>>> main

  private storeName = "audioBackups";
  private chunksStoreName = "audioChunks";

  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

<<<<<<< HEAD
      request.onerror = () => {
        console.error("❌ Failed to open IndexedDB:", request.error);
        reject(new Error("Failed to open IndexedDB"));
=======
      request.onerror = (event) => {
        const errorMsg = (event.target as IDBOpenDBRequest).error?.message || "Unknown error";
        const error = new Error(`Failed to open IndexedDB: ${errorMsg}`);
        console.error("[IndexedDB] Open error:", error);
        Sentry.captureException(error);
        reject(error);
>>>>>>> main
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log("[IndexedDB] Successfully opened database");
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        console.log("[IndexedDB] Upgrading database to version", this.version);

        // Create audioBackups store if it doesn't exist
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: "id" });
          store.createIndex("timestamp", "timestamp", { unique: false });
          console.log("[IndexedDB] Created object store");
        }

        // Create audioChunks store for streaming chunks
        if (!db.objectStoreNames.contains(this.chunksStoreName)) {
          const chunksStore = db.createObjectStore(this.chunksStoreName, { keyPath: ["id", "chunkIndex"] });
          chunksStore.createIndex("id", "id", { unique: false });
          chunksStore.createIndex("timestamp", "timestamp", { unique: false });
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

  // STREAMING METHODS: Stream chunks directly to IndexedDB
  async appendChunk(backupId: string, chunkIndex: number, chunkData: Blob): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.chunksStoreName], "readwrite");
      const store = transaction.objectStore(this.chunksStoreName);
      
      const chunk: AudioChunk = {
        id: backupId,
        chunkIndex,
        data: chunkData,
        timestamp: Date.now(),
      };
      
      const request = store.put(chunk);

      request.onerror = () => {
        console.error("❌ Failed to save audio chunk:", request.error);
        reject(new Error("Failed to save audio chunk"));
      };

      request.onsuccess = () => {
        resolve();
      };
    });
  }

  async getChunks(backupId: string): Promise<AudioChunk[]> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.chunksStoreName], "readonly");
      const store = transaction.objectStore(this.chunksStoreName);
      const index = store.index("id");
      const request = index.getAll(backupId);

      request.onerror = () => {
        reject(new Error("Failed to get audio chunks"));
      };

      request.onsuccess = () => {
        // Sort chunks by chunkIndex to ensure correct order
        const chunks = request.result.sort((a, b) => a.chunkIndex - b.chunkIndex);
        resolve(chunks);
      };
    });
  }

  async reconstructBlob(backupId: string, mimeType: string): Promise<Blob> {
    const chunks = await this.getChunks(backupId);
    const blobParts = chunks.map(chunk => chunk.data);
    return new Blob(blobParts, { type: mimeType });
  }

  async deleteChunks(backupId: string): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.chunksStoreName], "readwrite");
      const store = transaction.objectStore(this.chunksStoreName);
      const index = store.index("id");
      const request = index.openCursor(IDBKeyRange.only(backupId));

      request.onerror = () => {
        reject(new Error("Failed to delete audio chunks"));
      };

      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };
    });
  }

  // DEBUGGING: Check IndexedDB status and list all chunks
  async debugIndexedDB(): Promise<void> {
    try {
      await this.init();
      
      // List all chunks
      const transaction = this.db!.transaction([this.chunksStoreName], "readonly");
      const store = transaction.objectStore(this.chunksStoreName);
      const request = store.getAll();
      
      request.onsuccess = () => {
        const chunks = request.result;
        // Debug info available but not logged
      };
      
      request.onerror = () => {
        // Error handled silently
      };
    } catch (err) {
      // Debug error handled silently
    }
  }

  static generateBackupId(): string {
    return `backup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const audioBackupDB = new IndexedDBBackup();
export { IndexedDBBackup };
export type { AudioBackup, AudioChunk };
