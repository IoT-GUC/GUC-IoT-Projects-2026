const env = process.env
const path = require('path')

const oracledb = require('oracledb')

oracledb.outFormat = oracledb.OUT_FORMAT_OBJECT

async function initialize() {
    try {
        await oracledb.createPool({
            user: env.ORACLE_DB_USER,
            password: env.ORACLE_DB_PASSWORD,
            connectString: env.ORACLE_DB_CONNECT_STRING,
            configDir: path.join(__dirname, 'wallet'),
            walletLocation: path.join(__dirname, 'wallet'),
            walletPassword: env.ORACLE_DB_PASSWORD,
            poolMin: parseInt(env.DB_POOL_MIN) || 1,
            poolMax: parseInt(env.DB_POOL_MAX) || 10,
            poolIncrement: parseInt(env.DB_POOL_INC) || 1
        })
        console.log('Connected to Oracle Database')
        return true
    } catch (err) {
        console.error(err)
        return false
    }
}

async function closePool() {
    await oracledb.getPool().close(10)
}

async function query(sql, binds = [], options = {}) {
    let connection

    try {
        connection = await oracledb.getConnection()

        const result = await connection.execute(sql, binds, options)
        return result
    } catch (err) {
        return { error: err }
    } finally {
        if (connection) {
            try {
                await connection.close()
            } catch (err) {

            }
        }
    }
}

module.exports = {
    initialize,
    closePool,
    query
}
