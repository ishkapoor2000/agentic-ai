window.MERMAID_GRAPH_DATA = `
graph TD
  subgraph agentic_doc["agentic_doc"]
    file_18["config.py"]
    sym_30[class: Config]
    file_18 --> sym_30
    sym_31[function: load_config]
    file_18 --> sym_31
    sym_32[function: save_config]
    file_18 --> sym_32
    file_19["cli.py"]
    sym_33[function: init]
    file_19 --> sym_33
    sym_34[function: scan]
    file_19 --> sym_34
    sym_35[function: doc]
    file_19 --> sym_35
    sym_36[function: graph]
    file_19 --> sym_36
    sym_37[function: serve]
    file_19 --> sym_37
  end
  subgraph agentic_doc_analysis["agentic_doc/analysis"]
    file_24["python.py"]
    sym_57[class: PythonAnalyzer]
    file_24 --> sym_57
    sym_58[method: PythonAnalyzer.analyze]
    file_24 --> sym_58
    sym_59[class: SymbolVisitor]
    file_24 --> sym_59
    sym_60[method: SymbolVisitor.__init__]
    file_24 --> sym_60
    sym_61[method: SymbolVisitor._get_docstring]
    file_24 --> sym_61
    file_25["javascript.py"]
    sym_70[class: JavaScriptAnalyzer]
    file_25 --> sym_70
    sym_71[method: JavaScriptAnalyzer.analyze]
    file_25 --> sym_71
    file_26["base.py"]
    sym_72[class: ExtractedSymbol]
    file_26 --> sym_72
    sym_73[class: ExtractedReference]
    file_26 --> sym_73
    sym_74[class: AnalysisResult]
    file_26 --> sym_74
    sym_75[class: BaseAnalyzer]
    file_26 --> sym_75
    sym_76[method: BaseAnalyzer.analyze]
    file_26 --> sym_76
  end
  subgraph agentic_doc_core["agentic_doc/core"]
    file_22["doc_builder.py"]
    sym_50[class: DocBuilder]
    file_22 --> sym_50
    sym_51[method: DocBuilder.__init__]
    file_22 --> sym_51
    sym_52[method: DocBuilder.generate_file_docs]
    file_22 --> sym_52
    sym_53[method: DocBuilder._process_file]
    file_22 --> sym_53
    sym_54[method: DocBuilder.generate_dir_docs]
    file_22 --> sym_54
    file_23["prompts.py"]
  end
  subgraph agentic_doc_db["agentic_doc/db"]
    file_27["session.py"]
    sym_77[function: create_db_and_tables]
    file_27 --> sym_77
    sym_78[function: get_session]
    file_27 --> sym_78
    file_28["schema.py"]
    sym_79[class: File]
    file_28 --> sym_79
    sym_80[class: Directory]
    file_28 --> sym_80
    sym_81[class: Symbol]
    file_28 --> sym_81
    sym_82[class: Reference]
    file_28 --> sym_82
    sym_83[class: LLMCache]
    file_28 --> sym_83
  end
  subgraph agentic_doc_indexer["agentic_doc/indexer"]
    file_29["core.py"]
    sym_84[class: Indexer]
    file_29 --> sym_84
    sym_85[method: Indexer.__init__]
    file_29 --> sym_85
    sym_86[method: Indexer._load_ignore_spec]
    file_29 --> sym_86
    sym_87[method: Indexer.should_ignore]
    file_29 --> sym_87
    sym_88[method: Indexer.get_file_hash]
    file_29 --> sym_88
  end
  subgraph agentic_doc_llm["agentic_doc/llm"]
    file_20["core.py"]
    sym_38[class: LLMClient]
    file_20 --> sym_38
    sym_39[method: LLMClient.__init__]
    file_20 --> sym_39
    sym_40[method: LLMClient._hash_prompt]
    file_20 --> sym_40
    sym_41[method: LLMClient.generate]
    file_20 --> sym_41
    file_21["providers.py"]
    sym_42[class: ModelProvider]
    file_21 --> sym_42
    sym_43[method: ModelProvider.generate]
    file_21 --> sym_43
    sym_44[class: OpenAIProvider]
    file_21 --> sym_44
    sym_45[method: OpenAIProvider.__init__]
    file_21 --> sym_45
    sym_46[method: OpenAIProvider.generate]
    file_21 --> sym_46
  end
  subgraph app_api_v1["app/api/v1"]
    file_43["users.py"]
    file_44["router.py"]
  end
  subgraph app_core["app/core"]
    file_38["config.py"]
    file_39["security.py"]
  end
  subgraph app_db["app/db"]
    file_42["database.py"]
  end
  subgraph app_models["app/models"]
    file_40["user.py"]
    file_41["product.py"]
  end
  subgraph app_services["app/services"]
    file_45["user_service.py"]
  end
  subgraph frontend_components["frontend/components"]
    file_47["LoginForm.jsx"]
    file_48["ProductCard.jsx"]
  end
  subgraph frontend_services["frontend/services"]
    file_49["authService.js"]
  end
  subgraph frontend_utils["frontend/utils"]
    file_46["helpers.js"]
  end
  subgraph root["root"]
    file_3["pyproject.toml"]
    file_30[".agentic-doc.yml"]
    file_31[".DS_Store"]
    file_34["switch_provider.sh"]
    file_35["README.md"]
    file_36["GEMINI_SETUP.md"]
    file_37["main.py"]
    file_51["TEST_COMPLETE.sh"]
    file_58["agentic_doc.db"]
    file_59["graph.json"]
    file_60["graph.mmd"]
  end`;
