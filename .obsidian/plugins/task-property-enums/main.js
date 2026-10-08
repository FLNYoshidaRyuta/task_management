"use strict";

const { Plugin, TFile } = require("obsidian");

const CHOICES_PATH = "tasks/_config/property-choices.json";
const SELECT_CLASS = "custom-task-enum-select";

class TaskPropertyEnumsPlugin extends Plugin {
  choices = {};
  observer = null;

  async onload() {
    await this.loadChoices();
    this.observer = new MutationObserver(() => {
      this.injectDropdowns(document.body);
    });
    this.app.workspace.onLayoutReady(() => {
      this.observer.observe(document.body, {
        childList: true,
        subtree: true,
      });
      this.injectDropdowns(document.body);
    });
  }

  onunload() {
    this.observer?.disconnect();
  }

  async loadChoices() {
    try {
      const raw = await this.app.vault.adapter.read(CHOICES_PATH);
      this.choices = JSON.parse(raw);
    } catch (error) {
      console.error("task-property-enums: failed to load choices", error);
      this.choices = {};
    }
  }

  getFileFromElement(el) {
    const leafEl = el.closest(".workspace-leaf");
    if (!leafEl) {
      return this.app.workspace.getActiveFile();
    }

    let targetFile = null;
    this.app.workspace.iterateAllLeaves((leaf) => {
      if (leaf.view.containerEl.parentElement === leafEl) {
        const view = leaf.view;
        if ("file" in view && view.file instanceof TFile) {
          targetFile = view.file;
        }
      }
    });
    return targetFile ?? this.app.workspace.getActiveFile();
  }

  readCurrentValue(file, key) {
    if (!(file instanceof TFile)) {
      return "";
    }
    const cache = this.app.metadataCache.getFileCache(file);
    const raw = cache?.frontmatter?.[key];
    if (Array.isArray(raw)) {
      return typeof raw[0] === "string" ? raw[0] : "";
    }
    if (typeof raw === "string") {
      return raw;
    }
    return "";
  }

  async writeValue(file, key, newValue) {
    if (!(file instanceof TFile)) {
      return;
    }
    await this.app.fileManager.processFrontMatter(file, (frontmatter) => {
      frontmatter[key] = newValue ? [newValue] : [];
    });
  }

  buildSelect(key, options, currentValue, onChange) {
    const selectEl = document.createElement("select");
    selectEl.classList.add(SELECT_CLASS);
    selectEl.setAttribute("aria-label", `Select value for ${key}`);

    const emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.text = "---";
    selectEl.appendChild(emptyOpt);

    options.forEach((opt) => {
      const optionEl = document.createElement("option");
      optionEl.value = opt;
      optionEl.text = opt;
      if (opt === currentValue) {
        optionEl.selected = true;
      }
      selectEl.appendChild(optionEl);
    });

    selectEl.addEventListener("change", (event) => {
      const target = event.target;
      target.dataset.lastChanged = Date.now().toString();
      onChange(target.value);
    });

    return selectEl;
  }

  attachSelect(container, selectEl) {
    const stopInteraction = (event) => {
      event.stopPropagation();
    };
    ["mousedown", "mouseup", "click", "pointerdown", "pointerup", "focusin"].forEach(
      (name) => {
        selectEl.addEventListener(name, stopInteraction);
        selectEl.addEventListener(name, stopInteraction, { capture: true });
      }
    );
    container.appendChild(selectEl);
  }

  injectPropertiesDropdown(propEl, key, options) {
    const valueContainer = propEl.querySelector(".metadata-property-value");
    if (!valueContainer) {
      return;
    }

    const existing = valueContainer.querySelector(`.${SELECT_CLASS}`);
    const file = this.getFileFromElement(propEl);
    const currentValue = this.readCurrentValue(file, key);

    if (existing) {
      const lastChanged = parseInt(existing.dataset.lastChanged || "0", 10);
      if (Date.now() - lastChanged < 2000) {
        return;
      }
      if (existing.value !== currentValue) {
        existing.value = currentValue || "";
      }
      return;
    }

    Array.from(valueContainer.children).forEach((child) => {
      if (!child.classList.contains(SELECT_CLASS)) {
        child.classList.add("task-property-enums-hidden");
      }
    });

    const selectEl = this.buildSelect(key, options, currentValue, (newValue) => {
      this.writeValue(file, key, newValue);
    });
    selectEl.classList.add("mod-properties");
    this.attachSelect(valueContainer, selectEl);
  }

  injectBasesDropdown(cell, row, key, options) {
    const existing = cell.querySelector(`.${SELECT_CLASS}`);
    const link = row.querySelector(".internal-link");
    const href = link?.getAttribute("data-href");
    const file = href
      ? this.app.metadataCache.getFirstLinkpathDest(href, "")
      : null;
    const currentValue = this.readCurrentValue(file, key);

    if (existing) {
      const lastChanged = parseInt(existing.dataset.lastChanged || "0", 10);
      if (Date.now() - lastChanged < 2000) {
        return;
      }
      if (existing.value !== currentValue) {
        existing.value = currentValue || "";
      }
      return;
    }

    const selectEl = this.buildSelect(key, options, currentValue, (newValue) => {
      if (file instanceof TFile) {
        this.writeValue(file, key, newValue);
      }
    });
    selectEl.classList.add("mod-base");
    this.attachSelect(cell, selectEl);
  }

  injectDropdowns(container) {
    Object.entries(this.choices).forEach(([key, options]) => {
      if (!Array.isArray(options) || options.length === 0) {
        return;
      }

      container.querySelectorAll(".metadata-property").forEach((propEl) => {
        const keyEl = propEl.querySelector(".metadata-property-key-input");
        const propKey = keyEl?.value || keyEl?.textContent;
        if (propKey === key) {
          this.injectPropertiesDropdown(propEl, key, options);
        }
      });

      const dataProperty = `note.${key}`;
      container.querySelectorAll(`.bases-td[data-property="${dataProperty}"]`).forEach(
        (cellEl) => {
          const row = cellEl.closest(".bases-tr");
          if (!row) {
            return;
          }
          this.injectBasesDropdown(cellEl, row, key, options);
        }
      );
    });
  }
}

module.exports = TaskPropertyEnumsPlugin;
