import { describe, expect, it } from "vitest";
import { extractBookingEntities } from "./booking-extractor";

describe("extractBookingEntities", () => {
  it("extrai hotel e companhia aérea da tabela de custos do roteiro", () => {
    const sample = `
# Lisboa em 3 dias

A base de hospedagem é o **NH Lisboa Campo Grande**.

## Tabela de Custos Detalhada em EUR (€)

| Item | Descrição | Tarifa unitária | Total estimado |
|---|---|---|---|
| **Voo** | **TAP Air Portugal** (ida e volta, via conexão com Azul – trecho Ipatinga → Lisboa sem voo direto) | € 1.200,00 | **€ 1.200,00** |
| **Hotel** | **NH Lisboa Campo Grande** – 4 estrelas, com café da manhã e Wi-Fi | € 75,00/noite | **€ 225,00** (3 noites) |
| **Alimentação/dia** | Café: pastelaria/pão e café (€ 6,00) | € 40,00/dia | **€ 120,00** (3 dias) |
`;

    const extracted = extractBookingEntities(sample);

    expect(extracted.hotelName).toBe("NH Lisboa Campo Grande");
    expect(extracted.hotelStars).toBe("4 estrelas");
    expect(extracted.transportCompany).toBe("TAP Air Portugal");
  });

  it("extrai dados quando não há tabela mas há menções no texto", () => {
    const sample = "Recomendamos a hospedagem no **Copacabana Palace** e voo pela **GOL**.";
    const extracted = extractBookingEntities(sample);

    expect(extracted.hotelName).toBe("Copacabana Palace");
    expect(extracted.transportCompany).toBe("GOL");
  });

  it("retorna objeto vazio para markdown sem correspondências", () => {
    expect(extractBookingEntities("")).toEqual({});
    expect(extractBookingEntities("Texto simples sem entidades")).toEqual({});
  });
});
