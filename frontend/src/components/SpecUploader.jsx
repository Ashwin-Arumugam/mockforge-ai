import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';

export default function SpecUploader({ activeProjectId, onSpecUploaded }) {
  const [rawSpec, setRawSpec] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const sampleYaml = `openapi: 3.0.3
info:
  title: Complete E-Commerce & Retail Platform API
  version: 1.5.0
  description: Comprehensive E-Commerce API with Users, Products, Orders, Payments, and Checkout
paths:
  /users:
    post:
      summary: Register Customer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      responses:
        '201': { description: Customer Created }
    get:
      summary: List Customers
      responses:
        '200': { description: List of Customers }
  /users/{id}:
    get:
      summary: Get Customer Details
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: Customer Found }
  /products:
    post:
      summary: Add New Product
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Product'
      responses:
        '201': { description: Product Added }
    get:
      summary: Catalog Search
      responses:
        '200': { description: List of Products }
  /orders:
    post:
      summary: Place New Order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Order'
      responses:
        '201': { description: Order Placed }
    get:
      summary: List All Orders
      responses:
        '200': { description: Orders List }
  /orders/{id}:
    patch:
      summary: Update Order Status
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: Status Updated }
  /users/{userId}/orders:
    get:
      summary: Get Customer Orders
      parameters:
        - name: userId
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: List of Customer Orders }
  /payments:
    post:
      summary: Process Payment Gateway Transaction
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Payment'
      responses:
        '200': { description: Payment Successful }
  /checkout:
    post:
      summary: Complete Cart Checkout
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id, payment_method]
              properties:
                user_id: { type: string }
                payment_method: { type: string }
      responses:
        '200': { description: Checkout Processed }
components:
  schemas:
    User:
      type: object
      required: [name, email]
      properties:
        id: { type: string }
        name: { type: string }
        email: { type: string }
    Product:
      type: object
      required: [title, price]
      properties:
        id: { type: string }
        title: { type: string }
        price: { type: number }
    Order:
      type: object
      required: [user_id, total]
      properties:
        id: { type: string }
        user_id: { type: string }
        total: { type: number }
        status:
          type: string
          enum: [CREATED, PAID, SHIPPED, DELIVERED, CANCELLED]
          default: CREATED
    Payment:
      type: object
      required: [order_id, amount]
      properties:
        id: { type: string }
        order_id: { type: string }
        amount: { type: number }
        currency: { type: string, default: USD }`;

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setRawSpec(event.target.result);
    };
    reader.readAsText(file);
  };

  const handleUpload = async () => {
    if (!activeProjectId) {
      setStatusMsg({ type: 'error', text: 'Please select or create a project first.' });
      return;
    }

    const contentToUpload = rawSpec.trim() || sampleYaml;
    setIsUploading(true);
    setStatusMsg(null);

    try {
      const resp = await fetch(`/api/v1/specs/${activeProjectId}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_spec: contentToUpload })
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to upload OpenAPI spec');
      }

      setStatusMsg({
        type: 'success',
        text: `Spec Ingested! Extracted ${data.routes_count} endpoints & ${data.entities_discovered.length} entities.`
      });
      onSpecUploaded(data);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={20} color="#6366f1" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>1. Ingest OpenAPI Specification</h3>
        </div>
        <button
          className="btn-secondary"
          style={{ fontSize: '0.8rem', padding: '4px 10px' }}
          onClick={() => setRawSpec(sampleYaml)}
        >
          Load E-Commerce Sample
        </button>
      </div>

      <div style={{ marginBottom: '14px' }}>
        <textarea
          className="form-textarea"
          rows={8}
          placeholder="Paste OpenAPI 3.x YAML or JSON specification here..."
          value={rawSpec}
          onChange={(e) => setRawSpec(e.target.value)}
          style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label className="btn-secondary" style={{ cursor: 'pointer' }}>
          <Upload size={16} /> Choose .yaml / .json file
          <input type="file" accept=".yaml,.yml,.json" onChange={handleFileUpload} style={{ display: 'none' }} />
        </label>

        <button className="btn-primary" onClick={handleUpload} disabled={isUploading}>
          {isUploading ? 'Ingesting...' : 'Ingest Spec & Deploy Mock'} <ArrowRight size={16} />
        </button>
      </div>

      {statusMsg && (
        <div style={{
          marginTop: '14px', padding: '10px 14px', borderRadius: '8px',
          background: statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
          color: statusMsg.type === 'success' ? '#34d399' : '#f87171',
          border: '1px solid rgba(255,255,255,0.08)',
          fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          {statusMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{statusMsg.text}</span>
        </div>
      )}
    </div>
  );
}
