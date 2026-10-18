import csv
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Namespace fixo para geração determinística de UUIDs versão 5 (RFC 4122)
# NÃO ALTERAR ESTE UUID: a idempotência de todas as cargas depende dele.
NAMESPACE_LABVEPI = uuid.UUID("6f1c0b5e-0000-4000-8000-00000000abcd")

def id_estavel(planilha: str, chave: Any) -> str:
    """
    Gera um UUIDv5 determinístico a partir do nome da planilha e de uma chave única.
    
    A mesma combinação de planilha e chave sempre gera o mesmo identificador universal.
    Isso assegura que reexecutar o extrator de ETL não duplica registros.
    
    Exemplos:
        id_estavel("morcegos", "M01") -> "e2e9c2f6-..."
        id_estavel("aves", 15)        -> "a84b12c1-..."
    """
    chave_limpa = str(chave).strip()
    return str(uuid.uuid5(NAMESPACE_LABVEPI, f"{planilha}:{chave_limpa}"))

@dataclass
class ProblemaItem:
    linha: int
    coluna: str
    valor: Any
    motivo: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "linha": self.linha,
            "coluna": self.coluna,
            "valor": "" if self.valor is None else str(self.valor),
            "motivo": self.motivo,
        }

@dataclass
class Resultado:
    """
    Contêiner acumulador do resultado da extração e transformação de uma planilha.
    
    Armazena coleções de entidades canônicas estruturadas (animais, amostras, exames)
    e um registro detalhado de anomalias/inconsistências encontradas para auditoria humana.
    """
    animais: List[Dict[str, Any]] = field(default_factory=list)
    amostras: List[Dict[str, Any]] = field(default_factory=list)
    exames: List[Dict[str, Any]] = field(default_factory=list)
    problemas: List[ProblemaItem] = field(default_factory=list)
    _proximo_id_animal: int = 1
    _proximo_id_amostra: int = 1
    _proximo_id_exame: int = 1

    def proximo_id_animal(self) -> int:
        """Retorna o próximo identificador numérico autoincremental para Animal."""
        pid = self._proximo_id_animal
        self._proximo_id_animal += 1
        return pid

    def proximo_id_amostra(self) -> int:
        """Retorna o próximo identificador numérico autoincremental para Amostra."""
        pid = self._proximo_id_amostra
        self._proximo_id_amostra += 1
        return pid

    def proximo_id_exame(self) -> int:
        """Retorna o próximo identificador numérico autoincremental para Exame."""
        pid = self._proximo_id_exame
        self._proximo_id_exame += 1
        return pid

    def registrar_problema(self, linha: int, coluna: str, valor: Any, motivo: str) -> None:
        """Registra uma incoerência na planilha para revisão laboratorial."""
        self.problemas.append(ProblemaItem(linha=linha, coluna=coluna, valor=valor, motivo=motivo))

    # Alias amigável curto
    problema = registrar_problema

    def salvar(self, diretorio_saida: Union[str, Path]) -> Dict[str, int]:
        """
        Exporta as listas de entidades para arquivos .jsonl e o log de problemas para .csv.
        
        Gera no diretório indicado:
        - animais.jsonl (se houver animais)
        - amostras.jsonl (se houver amostras)
        - exames.jsonl (se houver exames)
        - problemas.csv (com todas as anomalias detectadas)
        
        Retorna:
            Dicionário com a contagem dos itens exportados.
        """
        caminho_dir = Path(diretorio_saida)
        caminho_dir.mkdir(parents=True, exist_ok=True)

        contagens = {
            "animais": len(self.animais),
            "amostras": len(self.amostras),
            "exames": len(self.exames),
            "problemas": len(self.problemas),
        }

        # 1. Salvar animais.jsonl
        if self.animais:
            arq_animais = caminho_dir / "animais.jsonl"
            with open(arq_animais, "w", encoding="utf-8") as f:
                for doc in self.animais:
                    f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")

        # 2. Salvar amostras.jsonl
        if self.amostras:
            arq_amostras = caminho_dir / "amostras.jsonl"
            with open(arq_amostras, "w", encoding="utf-8") as f:
                for doc in self.amostras:
                    f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")

        # 3. Salvar exames.jsonl
        if self.exames:
            arq_exames = caminho_dir / "exames.jsonl"
            with open(arq_exames, "w", encoding="utf-8") as f:
                for doc in self.exames:
                    f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")

        # 4. Salvar problemas.csv (sempre gerado para evidenciar conformidade ou falhas)
        arq_problemas = caminho_dir / "problemas.csv"
        with open(arq_problemas, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["linha", "coluna", "valor", "motivo"])
            writer.writeheader()
            for p in self.problemas:
                writer.writerow(p.to_dict())

        return contagens